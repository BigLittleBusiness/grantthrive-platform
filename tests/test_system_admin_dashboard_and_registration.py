import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app import create_app, db
from app.models import Council, Grant, PublicSubmission, User
from app.system_admin.admin_auth import _generate_admin_token
from config.config import TestingConfig


class SystemAdminTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SECRET_KEY = "system-admin-dashboard-test-secret"
    TURNSTILE_TEST_BYPASS = True
    PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED = False


class SystemAdminDashboardAndRegistrationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SystemAdminTestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _system_admin_headers(self):
        admin = User(
            username="platform_admin",
            email="platform.admin@example.invalid",
            password_hash="unused-in-token-test",
            first_name="Platform",
            last_name="Administrator",
            role="system_admin",
            is_active=True,
            is_approved=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"Authorization": f"Bearer {_generate_admin_token(admin)}"}

    def test_dashboard_uses_live_records_for_counts_and_action_items(self):
        headers = self._system_admin_headers()
        council = Council(name="Example Council", subdomain="example", slug="example", is_active=True)
        db.session.add(council)
        db.session.flush()

        pending_admin = User(
            username="pending_council_admin",
            email="pending@example.gov.au",
            password_hash="unused",
            first_name="Pending",
            last_name="Council",
            role="council_admin",
            is_active=False,
            is_approved=False,
        )
        grant_creator = User(
            username="grant_creator",
            email="creator@example.gov.au",
            password_hash="unused",
            first_name="Grant",
            last_name="Creator",
            role="council_admin",
            council_id=council.id,
            is_active=True,
            is_approved=True,
        )
        db.session.add_all([pending_admin, grant_creator])
        db.session.flush()
        db.session.add(Grant(
            council_id=council.id,
            title="Live grant",
            description="A live dashboard test grant.",
            category="Community",
            total_budget=10000,
            opens_at=datetime.now(timezone.utc),
            closes_at=datetime.now(timezone.utc) + timedelta(days=30),
            created_by=grant_creator.id,
            status="draft",
        ))
        db.session.add_all([
            PublicSubmission(
                submission_type="contact",
                contact_type="general",
                status="new",
                name="Jordan Example",
                email="jordan@example.com",
                notification_status="sent",
            ),
            PublicSubmission(
                submission_type="waitlist",
                status="resolved",
                name="Taylor Example",
                email="taylor@example.com",
                notification_status="failed",
            ),
        ])
        db.session.commit()

        response = self.client.get("/api/admin/dashboard", headers=headers)

        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertEqual(body["stats"]["active_councils"], 1)
        self.assertEqual(body["stats"]["total_grants"], 1)
        self.assertEqual(body["stats"]["submitted_applications"], 0)
        alert_ids = {alert["id"] for alert in body["alerts"]}
        self.assertIn("pending-council-registrations", alert_ids)
        self.assertIn("new-form-submissions", alert_ids)
        self.assertIn("failed-form-notifications", alert_ids)
        self.assertTrue(body["recent_users"])

    @patch("app.common.email_service.send_council_registration_not_eligible", return_value=True)
    def test_non_council_email_is_not_registered_and_receives_guidance(self, send_guidance):
        response = self.client.post(
            "/api/auth/register/council",
            json={
                "first_name": "Jordan",
                "last_name": "Example",
                "email": "jordan@example.com",
                "password": "StrongPass!123",
                "organisation": "Example Organisation",
                "plan": "small",
                "billing_cycle": "monthly",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["code"], "council_email_required")
        self.assertEqual(User.query.filter_by(username="jordan").count(), 0)
        send_guidance.assert_called_once_with("jordan@example.com", "Jordan")

    @patch("app.common.email_service.send_email", return_value=True)
    def test_council_eligibility_email_uses_platform_subject_and_contact_form(self, send_email):
        from app.common.email_service import send_council_registration_not_eligible

        self.assertTrue(send_council_registration_not_eligible("jordan@example.com", "Jordan"))
        args, _kwargs = send_email.call_args
        self.assertEqual(args[0], "jordan@example.com")
        self.assertEqual(args[1], "GrantThrive - Council account registration information")
        self.assertIn("/contact", args[2])
        self.assertNotIn("mailto:", args[2])


if __name__ == "__main__":
    unittest.main()
