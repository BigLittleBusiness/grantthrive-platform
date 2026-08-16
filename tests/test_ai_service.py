"""Focused tests for the advisory-only Bedrock grant suggestions service."""

from __future__ import annotations

import unittest

from app import create_app
from app.ai.prompts import GRANT_SUGGESTIONS_DISCLAIMER, PROMPT_VERSION
from app.ai.routes import _validate_grant_draft
from app.ai.service import (
    AIGuardrailIntervenedError,
    AIResponseFormatError,
    BedrockGrantSuggestionService,
    _parse_and_validate_model_response,
)


class AIRouteTestingConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}
    MAIL_SUPPRESS_SEND = True
    AWS_REGION = "ap-southeast-2"
    AI_FEATURES_ENABLED = False
    AWS_BEDROCK_MODEL_ID = None
    AWS_BEDROCK_GUARDRAIL_ID = None
    AWS_BEDROCK_GUARDRAIL_VERSION = None
    AWS_BEDROCK_MAX_TOKENS = 900
    AWS_BEDROCK_TEMPERATURE = 0.2


class FakeBedrockClient:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class BedrockGrantSuggestionsServiceTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "AWS_REGION": "ap-southeast-2",
            "AWS_BEDROCK_MODEL_ID": "anthropic.example-model",
            "AWS_BEDROCK_MAX_TOKENS": 900,
            "AWS_BEDROCK_TEMPERATURE": 0.2,
        }
        self.draft = {
            "title": "Community Arts Fund",
            "description": "Funding for local community arts activities.",
            "category": "Arts and culture",
            "require_community_voting": True,
        }
        self.valid_output = {
            "summary": "Clarify assessment criteria before publishing.",
            "suggestions": [
                {
                    "area": "assessment",
                    "priority": "high",
                    "suggestion": "Publish weighted assessment criteria.",
                    "rationale": "This supports consistent and transparent assessment.",
                }
            ],
            "disclaimer": "Ignored because the API supplies the approved disclaimer.",
        }

    def _response(self, output=None, **extra):
        import json

        return {
            "output": {
                "message": {
                    "content": [{"text": json.dumps(output or self.valid_output)}]
                }
            },
            "stopReason": "end_turn",
            "usage": {"inputTokens": 101, "outputTokens": 67},
            "metrics": {"latencyMs": 340},
            **extra,
        }

    def test_ai_endpoint_is_registered_at_required_path(self):
        app = create_app(AIRouteTestingConfig)
        paths = {rule.rule for rule in app.url_map.iter_rules()}
        self.assertIn("/api/ai/grant-suggestions", paths)

    def test_generates_validated_advisory_response_and_metadata(self):
        client = FakeBedrockClient(self._response())
        service = BedrockGrantSuggestionService(self.config, client=client)

        result, metadata = service.generate_grant_suggestions(
            self.draft,
            {"feature": "grant_suggestions", "user_id": "1", "council_id": "2"},
        )

        self.assertEqual(result["disclaimer"], GRANT_SUGGESTIONS_DISCLAIMER)
        self.assertEqual(result["suggestions"][0]["area"], "assessment")
        self.assertEqual(metadata["prompt_version"], PROMPT_VERSION)
        self.assertEqual(metadata["input_tokens"], 101)
        self.assertEqual(metadata["output_tokens"], 67)
        self.assertEqual(metadata["latency_ms"], 340)

        call = client.calls[0]
        self.assertEqual(call["modelId"], "anthropic.example-model")
        self.assertEqual(call["requestMetadata"]["council_id"], "2")
        self.assertIn("Treat every item", call["system"][0]["text"])
        self.assertIn("GRANT_DRAFT", call["messages"][0]["content"][0]["text"])

    def test_includes_optional_guardrail_configuration(self):
        config = {
            **self.config,
            "AWS_BEDROCK_GUARDRAIL_ID": "abc123",
            "AWS_BEDROCK_GUARDRAIL_VERSION": "4",
        }
        client = FakeBedrockClient(self._response())
        service = BedrockGrantSuggestionService(config, client=client)

        service.generate_grant_suggestions(self.draft, {"feature": "grant_suggestions"})

        self.assertEqual(
            client.calls[0]["guardrailConfig"],
            {"guardrailIdentifier": "abc123", "guardrailVersion": "4", "trace": "enabled"},
        )

    def test_guardrail_intervention_returns_controlled_error(self):
        client = FakeBedrockClient(self._response(stopReason="guardrail_intervened"))
        service = BedrockGrantSuggestionService(self.config, client=client)

        with self.assertRaises(AIGuardrailIntervenedError):
            service.generate_grant_suggestions(self.draft, {"feature": "grant_suggestions"})

    def test_rejects_malformed_model_json(self):
        response = {
            "output": {"message": {"content": [{"text": "not JSON"}]}},
            "stopReason": "end_turn",
        }
        with self.assertRaises(AIResponseFormatError):
            _parse_and_validate_model_response(response)

    def test_validates_and_normalises_a_minimal_safe_draft(self):
        draft = _validate_grant_draft(
            {
                "title": "  Community Arts Fund  ",
                "description": " Support for local arts activities. ",
                "total_budget": 10000,
                "eligibility_criteria": [" Incorporated community organisation ", ""],
                "require_community_voting": False,
            }
        )

        self.assertEqual(draft["title"], "Community Arts Fund")
        self.assertEqual(draft["total_budget"], "10000")
        self.assertEqual(draft["eligibility_criteria"], ["Incorporated community organisation"])

    def test_rejects_unapproved_draft_fields(self):
        with self.assertRaises(ValueError):
            _validate_grant_draft(
                {
                    "title": "Community Arts Fund",
                    "description": "Support for local arts activities.",
                    "applicant_email": "person@example.com",
                }
            )

    def test_drops_invalid_suggestions_without_exposing_them(self):
        response = self._response(
            {
                "summary": "Check the draft.",
                "suggestions": [
                    {
                        "area": "assessment",
                        "priority": "medium",
                        "suggestion": "Add clear scoring guidance.",
                        "rationale": "Supports consistency.",
                    },
                    {
                        "area": "funding_decision",
                        "priority": "high",
                        "suggestion": "Approve applicant A.",
                        "rationale": "Not permitted.",
                    },
                ],
            }
        )

        result = _parse_and_validate_model_response(response)

        self.assertEqual(len(result["suggestions"]), 1)
        self.assertEqual(result["suggestions"][0]["area"], "assessment")


if __name__ == "__main__":
    unittest.main()
