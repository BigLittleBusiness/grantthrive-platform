"""Focused coverage for the role-scoped Help & Guidance API."""

import unittest

from app import create_app, db
from app.auth.helpers import _generate_token
from app.models import User
from app.support.knowledge_base import COHORTS
from app.system_admin.admin_auth import _generate_admin_token
from config.config import TestingConfig


class SupportGuidanceTestingConfig(TestingConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    SECRET_KEY = "support-guidance-test-secret-at-least-32-bytes"
    PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED = False


class SupportGuidanceTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SupportGuidanceTestingConfig)
        self.context = self.app.app_context()
        self.context.push()
        db.create_all()
        self.client = self.app.test_client()
        self.system_admin = self._user("system-admin", "system.admin@example.invalid", "system_admin")
        self.council_admin = self._user("council-admin", "council.admin@example.invalid", "council_admin")
        self.council_staff = self._user("council-staff", "council.staff@example.invalid", "council_staff")
        self.community_member = self._user("community-member", "community@example.invalid", "community_member")
        self.consultant = self._user("consultant", "consultant@example.invalid", "professional_consultant")
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def _user(self, username, email, role):
        user = User(
            username=username,
            email=email,
            password_hash="unused",
            first_name=username,
            last_name="Test",
            role=role,
            is_active=True,
            is_approved=True,
        )
        db.session.add(user)
        db.session.flush()
        return user

    def _headers(self, user):
        if user.role == "system_admin":
            token = _generate_admin_token(user)
        else:
            token = _generate_token(user)
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _question_ids(payload):
        return {
            question["id"]
            for cohort in payload["cohorts"]
            for question in cohort["questions"]
        }

    def test_knowledge_base_has_six_complete_approved_cohorts(self):
        self.assertEqual(len(COHORTS), 6)
        self.assertEqual(sum(len(cohort["questions"]) for cohort in COHORTS), 180)
        self.assertTrue(all(len(cohort["questions"]) == 30 for cohort in COHORTS))
        final_public_answer = COHORTS[-1]["questions"][-1]["answer"]
        self.assertNotIn("Document control", final_public_answer)
        self.assertNotIn("This guide contains 180 role-specific", final_public_answer)

    def test_anonymous_response_is_public_visitor_only(self):
        response = self.client.get("/api/support/guidance")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"], {
            "role": "public_visitor",
            "label": "Public Visitor",
            "authenticated": False,
            "cohorts": ["public_visitor"],
        })
        self.assertEqual(payload["total_questions"], 30)
        self.assertEqual(len(payload["cohorts"]), 1)
        self.assertEqual(len(payload["cohorts"][0]["questions"]), 30)
        questions = payload["cohorts"][0]["questions"]
        self.assertNotIn(
            "How do I sign in to the System Administration dashboard?",
            [question["question"] for question in questions],
        )
        self.assertTrue(all(question["id"].startswith("public_visitor-") for question in questions))

    def test_invalid_bearer_token_returns_normal_401(self):
        response = self.client.get(
            "/api/support/guidance",
            headers={"Authorization": "Bearer not-a-valid-token"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.get_json(), {"error": "Invalid token."})

    def test_system_admin_gets_only_admin_guidance_top_ten_and_admin_topics(self):
        response = self.client.get("/api/support/guidance", headers=self._headers(self.system_admin))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["role"], "system_admin")
        self.assertTrue(payload["actor"]["authenticated"])
        self.assertEqual(payload["actor"]["cohorts"], ["system_administrator"])
        self.assertEqual(payload["total_questions"], 30)
        self.assertEqual(len(payload["cohorts"][0]["questions"]), 30)
        self.assertEqual(len(payload["top_questions"]), 10)
        self.assertTrue(all(item["cohort_id"] == "system_administrator" for item in payload["top_questions"]))
        topic_ids = {topic["id"] for topic in payload["contextual_topics"]}
        self.assertIn("mfa-security", topic_ids)
        self.assertNotIn("application-documents", topic_ids)
        allowed_ids = self._question_ids(payload)
        self.assertTrue(all(
            set(topic["question_ids"]).issubset(allowed_ids)
            for topic in payload["contextual_topics"]
        ))

    def test_council_admin_never_receives_system_content_and_topics_are_scoped(self):
        response = self.client.get("/api/support/guidance", headers=self._headers(self.council_admin))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["cohorts"], ["council_administrator"])
        self.assertEqual(payload["total_questions"], 30)
        returned_ids = self._question_ids(payload)
        self.assertTrue(all(question_id.startswith("council_administrator-") for question_id in returned_ids))
        self.assertNotIn("system_administrator-01", returned_ids)
        self.assertIn("reports-exports", {topic["id"] for topic in payload["contextual_topics"]})
        self.assertTrue(all(
            set(topic["question_ids"]).issubset(returned_ids)
            for topic in payload["contextual_topics"]
        ))

    def test_council_staff_gets_assessor_guidance_only(self):
        response = self.client.get("/api/support/guidance", headers=self._headers(self.council_staff))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["cohorts"], ["council_staff_assessor"])
        self.assertEqual(payload["total_questions"], 30)
        self.assertTrue(all(
            question_id.startswith("council_staff_assessor-")
            for question_id in self._question_ids(payload)
        ))
        self.assertEqual(len(payload["top_questions"]), 10)
        self.assertIn("reviewer-assignment", {topic["id"] for topic in payload["contextual_topics"]})
        self.assertNotIn("reports-exports", {topic["id"] for topic in payload["contextual_topics"]})

    def test_community_member_gets_applicant_and_community_guidance_but_ten_top_items(self):
        response = self.client.get("/api/support/guidance", headers=self._headers(self.community_member))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["cohorts"], ["applicant", "community_member"])
        self.assertEqual(payload["total_questions"], 60)
        self.assertEqual([len(cohort["questions"]) for cohort in payload["cohorts"]], [30, 30])
        self.assertEqual(len(payload["top_questions"]), 10)
        self.assertEqual(
            {item["cohort_id"] for item in payload["top_questions"]},
            {"applicant", "community_member"},
        )
        self.assertEqual(
            sum(item["cohort_id"] == "applicant" for item in payload["top_questions"]),
            5,
        )
        self.assertEqual(
            sum(item["cohort_id"] == "community_member" for item in payload["top_questions"]),
            5,
        )

    def test_professional_consultant_gets_applicant_guidance_only(self):
        response = self.client.get("/api/support/guidance", headers=self._headers(self.consultant))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["role"], "professional_consultant")
        self.assertEqual(payload["actor"]["label"], "Applicant")
        self.assertEqual(payload["actor"]["cohorts"], ["applicant"])
        self.assertEqual(payload["total_questions"], 30)
        self.assertTrue(all(question_id.startswith("applicant-") for question_id in self._question_ids(payload)))
        self.assertTrue(all(item["cohort_id"] == "applicant" for item in payload["top_questions"]))

    def test_unmapped_future_role_fails_closed_with_no_guidance(self):
        unmapped_user = self._user("unmapped", "unmapped@example.invalid", "future_role")
        db.session.commit()

        response = self.client.get("/api/support/guidance", headers=self._headers(unmapped_user))
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        self.assertEqual(payload["actor"]["role"], "future_role")
        self.assertEqual(payload["actor"]["cohorts"], [])
        self.assertEqual(payload["total_questions"], 0)
        self.assertEqual(payload["cohorts"], [])
        self.assertEqual(payload["top_questions"], [])
        self.assertEqual(payload["contextual_topics"], [])

    def test_full_text_query_filters_questions_and_top_questions_case_insensitively(self):
        response = self.client.get("/api/support/guidance?q=WAITLIST")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()

        returned_questions = [
            question
            for cohort in payload["cohorts"]
            for question in cohort["questions"]
        ]
        self.assertGreater(len(returned_questions), 0)
        self.assertTrue(all(
            "waitlist" in question["question"].casefold()
            or "waitlist" in question["answer"].casefold()
            for question in returned_questions
        ))
        self.assertTrue(all(
            "waitlist" in question["question"].casefold()
            or "waitlist" in question["answer"].casefold()
            for question in payload["top_questions"]
        ))


if __name__ == "__main__":
    unittest.main()
