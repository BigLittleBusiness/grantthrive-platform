import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app import create_app, db
from app.auth.helpers import _generate_token
from app.models import Application, CommunityVote, Council, Forum, ForumPost, Grant, User, VotingSession
from config.config import TestingConfig


class SecurityTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SECRET_KEY = "security-remediation-test-secret-at-least-32-bytes"
    PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED = False


class SecurityRemediationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SecurityTestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.council_a = Council(name="Alpha Council", subdomain="alpha", slug="alpha")
        self.council_b = Council(name="Bravo Council", subdomain="bravo", slug="bravo")
        db.session.add_all([self.council_a, self.council_b])
        db.session.flush()
        self.applicant_a = self._user("applicant-a", "applicant.a@example.invalid", "community_member", self.council_a.id)
        self.applicant_b = self._user("applicant-b", "applicant.b@example.invalid", "community_member", self.council_b.id)
        self.staff_a = self._user("staff-a", "staff.a@example.invalid", "council_staff", self.council_a.id)
        self.council_admin_a = self._user("council-admin-a", "council.admin.a@example.invalid", "council_admin", self.council_a.id)
        self.admin = self._user("admin", "admin@example.invalid", "system_admin", None)
        self.grant_a = self._grant(self.council_a, self.staff_a)
        self.grant_b = self._grant(self.council_b, self.applicant_b)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _user(self, username, email, role, council_id):
        user = User(username=username, email=email, password_hash="unused", first_name=username, last_name="Test", role=role, council_id=council_id, is_active=True, is_approved=True)
        db.session.add(user)
        db.session.flush()
        return user

    def _grant(self, council, creator):
        grant = Grant(council_id=council.id, title=f"{council.name} Grant", description="Test", category="Community", total_budget=1000, opens_at=datetime.now(timezone.utc)-timedelta(days=1), closes_at=datetime.now(timezone.utc)+timedelta(days=2), created_by=creator.id, status="open", is_published=True)
        db.session.add(grant)
        db.session.flush()
        return grant

    def _headers(self, user):
        return {"Authorization": f"Bearer {_generate_token(user)}"}

    def test_cross_tenant_application_create_is_rejected(self):
        response = self.client.post("/api/applications", headers=self._headers(self.applicant_a), json={"grant_id": self.grant_b.id, "organization_name": "Alpha applicant", "project_title": "Cross tenant", "project_description": "Must fail", "amount_requested": 100, "contact_person": "Example", "contact_email": "person@example.invalid"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Application.query.count(), 0)

    def test_cross_tenant_forum_post_edit_is_rejected(self):
        forum = Forum(council_id=self.council_a.id, title="Alpha forum", created_by=self.staff_a.id)
        db.session.add(forum)
        db.session.flush()
        post = ForumPost(forum_id=forum.id, author_id=self.staff_a.id, body="Original")
        db.session.add(post)
        db.session.commit()
        response = self.client.patch(f"/api/forums/{forum.id}/posts/{post.id}", headers=self._headers(self.applicant_b), json={"body": "Cross tenant edit"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(db.session.get(ForumPost, post.id).body, "Original")

    def test_unpublished_grant_is_hidden_from_map_and_impact(self):
        self.grant_a.is_published = False
        self.grant_a.latitude = -37.81
        self.grant_a.longitude = 144.96
        db.session.commit()
        collection = self.client.get("/api/mapping/grants-geojson")
        self.assertEqual(collection.status_code, 200)
        self.assertEqual(collection.get_json()["features"], [])
        impact = self.client.get(f"/api/mapping/grant-impact/{self.grant_a.id}")
        self.assertEqual(impact.status_code, 404)

    def test_map_requires_explicit_grant_display_consent_and_respects_council_filter(self):
        self.grant_a.latitude = -37.81
        self.grant_a.longitude = 144.96
        self.grant_a.location_name = "Alpha precinct"
        self.grant_a.enable_mapping = False
        db.session.commit()

        self.assertEqual(self.client.get("/api/mapping/grants-geojson").get_json()["features"], [])
        self.assertEqual(self.client.get(f"/api/mapping/grant-impact/{self.grant_a.id}").status_code, 404)

        self.grant_a.enable_mapping = True
        db.session.commit()
        collection = self.client.get(f"/api/mapping/grants-geojson?council_id={self.council_a.id}")
        self.assertEqual(collection.status_code, 200)
        features = collection.get_json()["features"]
        self.assertEqual(len(features), 1)
        self.assertEqual(features[0]["properties"]["id"], self.grant_a.id)
        self.assertEqual(features[0]["properties"]["location_name"], "Alpha precinct")

    def test_grant_map_location_is_validated_only_when_map_display_is_enabled(self):
        self.council_a.plan = "medium"
        db.session.commit()
        payload = {
            "title": "New Alpha Grant",
            "description": "A test grant",
            "category": "Community",
            "total_budget": 1000,
            "opens_at": "2026-10-01T00:00:00Z",
            "closes_at": "2026-12-01T00:00:00Z",
        }

        mapping_off = self.client.post("/api/grants", headers=self._headers(self.council_admin_a), json=payload)
        self.assertEqual(mapping_off.status_code, 201)
        created_id = mapping_off.get_json()["id"]

        mapping_on_without_location = self.client.patch(
            f"/api/grants/{created_id}",
            headers=self._headers(self.council_admin_a),
            json={"enable_mapping": True},
        )
        self.assertEqual(mapping_on_without_location.status_code, 400)
        self.assertIn("public location name", mapping_on_without_location.get_json()["error"].lower())

        mapping_on_with_location = self.client.patch(
            f"/api/grants/{created_id}",
            headers=self._headers(self.council_admin_a),
            json={
                "enable_mapping": True,
                "location_name": "Alpha civic precinct",
                "latitude": -37.81,
                "longitude": 144.96,
            },
        )
        self.assertEqual(mapping_on_with_location.status_code, 200)
        self.assertTrue(mapping_on_with_location.get_json()["enable_mapping"])

    def test_registration_required_vote_needs_authenticated_community_user(self):
        session = VotingSession(grant_id=self.grant_a.id, council_id=self.council_a.id, title="Voting", starts_at=datetime.now(timezone.utc)-timedelta(hours=1), ends_at=datetime.now(timezone.utc)+timedelta(hours=1), is_active=True, is_published=True, require_registration=True, created_by=self.staff_a.id)
        application = Application(grant_id=self.grant_a.id, applicant_id=self.applicant_a.id, organization_name="Applicant", project_title="Project", project_description="Project", amount_requested=100, contact_person="Person", contact_email="person@example.invalid", status="submitted")
        db.session.add_all([session, application])
        db.session.commit()
        response = self.client.post(f"/api/voting/sessions/{session.id}/vote", json={"application_id": application.id, "vote_value": 5})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(CommunityVote.query.count(), 0)

    @patch("app.system_admin.admin_auth.pyotp.random_base32", return_value="JBSWY3DPEHPK3PXP")
    def test_admin_mfa_setup_and_confirm_require_admin_scoped_token(self, _secret):
        from app.system_admin.admin_auth import _generate_admin_token
        headers = {"Authorization": f"Bearer {_generate_admin_token(self.admin)}"}
        response = self.client.post("/api/admin/mfa/setup", headers=headers)
        self.assertEqual(response.status_code, 200)
        import pyotp
        code = pyotp.TOTP("JBSWY3DPEHPK3PXP").now()
        confirmed = self.client.post("/api/admin/mfa/confirm", headers=headers, json={"code": code})
        self.assertEqual(confirmed.status_code, 200)
        self.assertTrue(db.session.get(User, self.admin.id).mfa_enabled)


if __name__ == "__main__":
    unittest.main()
