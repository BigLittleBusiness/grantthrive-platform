import unittest
from unittest.mock import patch

from app import create_app, db
from app.models import PublicSubmission, User
from app.system_admin.admin_auth import _generate_admin_token
from config.config import TestingConfig


class ContactFormsTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SECRET_KEY = "contact-form-test-secret"
    TURNSTILE_TEST_BYPASS = True
    PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED = False
    ADMIN_NOTIFICATION_EMAIL = "admin@example.invalid"
    ADMIN_DASHBOARD_URL = "https://admin.example.invalid/admin/dashboard"


class PublicContactFormTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(ContactFormsTestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _admin_headers(self):
        admin = User(
            username="platform_admin",
            email="admin@example.invalid",
            password_hash="unused-in-token-test",
            first_name="Platform",
            last_name="Administrator",
            role="system_admin",
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        return {"Authorization": f"Bearer {_generate_admin_token(admin)}"}

    @patch("app.contact.routes.email_service.send_public_submission_notification", return_value=True)
    def test_contact_persists_before_content_free_notification(self, notify):
        response = self.client.post(
            "/api/contact",
            json={
                "type": "support", "name": "Jordan Example", "email": "jordan@example.com",
                "organisation": "Example Council", "phone": "0400 000 000",
                "message": "Please help with our GrantThrive account.", "turnstile_token": "test-token",
            },
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["message"], "Thanks — your GrantThrive enquiry has been received.")
        submission = PublicSubmission.query.one()
        self.assertEqual((submission.submission_type, submission.contact_type, submission.status), ("contact", "support", "new"))
        self.assertEqual(submission.email, "jordan@example.com")
        self.assertEqual(submission.notification_status, "sent")
        notify.assert_called_once_with("admin@example.invalid", "https://admin.example.invalid/admin/dashboard")

    @patch("app.contact.routes.email_service.send_public_submission_notification", return_value=False)
    def test_waitlist_succeeds_when_notification_delivery_fails(self, notify):
        response = self.client.post(
            "/api/waitlist",
            json={"first_name": "Jordan", "email": "jordan@example.com", "turnstile_token": "test-token"},
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(PublicSubmission.query.one().notification_status, "failed")
        notify.assert_called_once()

    @patch("app.common.email_service.send_email", return_value=True)
    def test_notification_email_contains_only_secure_dashboard_link(self, send_email):
        from app.common.email_service import send_public_submission_notification
        self.assertTrue(send_public_submission_notification("admin@example.invalid", "https://admin.example.invalid/admin/dashboard"))
        args, _kwargs = send_email.call_args
        self.assertEqual(args[1], "GrantThrive - New form submission")
        self.assertIn("https://admin.example.invalid/admin/dashboard", args[2])
        self.assertNotIn("jordan@example.com", args[2])

    @patch("app.contact.routes.email_service.send_public_submission_notification", return_value=True)
    def test_system_admin_can_review_and_resolve_submission(self, _notify):
        created = self.client.post(
            "/api/waitlist",
            json={"first_name": "Jordan", "email": "jordan@example.com", "turnstile_token": "test-token"},
        )
        self.assertEqual(created.status_code, 201)
        submission = PublicSubmission.query.one()
        headers = self._admin_headers()
        listing = self.client.get("/api/admin/form-submissions", headers=headers)
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.get_json()["pagination"]["total"], 1)
        detail = self.client.get(f"/api/admin/form-submissions/{submission.id}", headers=headers)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.get_json()["submission"]["email"], "jordan@example.com")
        update = self.client.patch(
            f"/api/admin/form-submissions/{submission.id}", headers=headers,
            json={"status": "resolved", "internal_note": "Launch follow-up scheduled."},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.get_json()["submission"]["status"], "resolved")

    def test_contact_form_rejects_unknown_fields(self):
        response = self.client.post(
            "/api/contact",
            json={
                "type": "general", "name": "Jordan Example", "email": "jordan@example.com",
                "organisation": "", "phone": "", "message": "Hello", "turnstile_token": "test-token",
                "unexpected": "not accepted",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(PublicSubmission.query.count(), 0)

    def test_contact_form_rejects_missing_turnstile_when_bypass_disabled(self):
        self.app.config["TURNSTILE_TEST_BYPASS"] = False
        self.app.config["TURNSTILE_SECRET_KEY"] = ""
        response = self.client.post(
            "/api/contact",
            json={
                "type": "general", "name": "Jordan Example", "email": "jordan@example.com",
                "organisation": "", "phone": "", "message": "Hello", "turnstile_token": "",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Verification", response.get_json()["error"])
        self.assertEqual(PublicSubmission.query.count(), 0)


if __name__ == "__main__":
    unittest.main()
