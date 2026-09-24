import unittest
from unittest.mock import patch

from app import create_app
from config.config import TestingConfig


class ContactFormsTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SECRET_KEY = "contact-form-test-secret"
    TURNSTILE_TEST_BYPASS = True
    CONTACT_INBOX_EMAIL = "test-inbox@example.invalid"


class PublicContactFormTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(ContactFormsTestingConfig)
        self.client = self.app.test_client()

    @patch("app.contact.routes._audit")
    @patch("app.contact.routes.email_service.send_email", return_value=True)
    def test_contact_form_sends_branded_email_after_verification(self, send_email, _audit):
        response = self.client.post(
            "/api/contact",
            json={
                "type": "support",
                "name": "Jordan Example",
                "email": "jordan@example.com",
                "organisation": "Example Council",
                "phone": "0400 000 000",
                "message": "Please help with our GrantThrive account.",
                "turnstile_token": "test-token",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["message"], "Thanks — your GrantThrive enquiry has been sent.")
        args, kwargs = send_email.call_args
        self.assertEqual(args[0], "test-inbox@example.invalid")
        self.assertEqual(args[1], "GrantThrive - Support enquiry")
        self.assertEqual(kwargs["reply_to"], "jordan@example.com")

    @patch("app.contact.routes._audit")
    @patch("app.contact.routes.email_service.send_email", return_value=True)
    def test_waitlist_sends_branded_email_after_verification(self, send_email, _audit):
        response = self.client.post(
            "/api/waitlist",
            json={
                "first_name": "Jordan",
                "email": "jordan@example.com",
                "turnstile_token": "test-token",
            },
        )

        self.assertEqual(response.status_code, 201)
        args, kwargs = send_email.call_args
        self.assertEqual(args[1], "GrantThrive - Waitlist signup")
        self.assertEqual(kwargs["reply_to"], "jordan@example.com")

    @patch("app.contact.routes.email_service.send_email")
    def test_contact_form_rejects_unknown_fields(self, send_email):
        response = self.client.post(
            "/api/contact",
            json={
                "type": "general",
                "name": "Jordan Example",
                "email": "jordan@example.com",
                "organisation": "",
                "phone": "",
                "message": "Hello",
                "turnstile_token": "test-token",
                "unexpected": "not accepted",
            },
        )

        self.assertEqual(response.status_code, 400)
        send_email.assert_not_called()

    @patch("app.contact.routes.email_service.send_email")
    def test_contact_form_rejects_missing_turnstile_when_bypass_disabled(self, send_email):
        self.app.config["TURNSTILE_TEST_BYPASS"] = False
        self.app.config["TURNSTILE_SECRET_KEY"] = ""
        response = self.client.post(
            "/api/contact",
            json={
                "type": "general",
                "name": "Jordan Example",
                "email": "jordan@example.com",
                "organisation": "",
                "phone": "",
                "message": "Hello",
                "turnstile_token": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Verification", response.get_json()["error"])
        send_email.assert_not_called()


if __name__ == "__main__":
    unittest.main()
