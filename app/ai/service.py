"""AWS Bedrock service for GrantThrive's advisory-only AI features."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

try:
    import boto3
    from botocore.config import Config as BotoConfig
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:  # pragma: no cover
    boto3 = None
    BotoConfig = None
    BotoCoreError = Exception
    ClientError = Exception

from app.ai.prompts import (
    ALLOWED_PRIORITIES,
    ALLOWED_SUGGESTION_AREAS,
    GRANT_SUGGESTIONS_DISCLAIMER,
    GRANT_SUGGESTIONS_SYSTEM_PROMPT,
    MAX_RATIONALE_CHARACTERS,
    MAX_SUGGESTION_CHARACTERS,
    MAX_SUGGESTIONS,
    MAX_SUMMARY_CHARACTERS,
    PROMPT_VERSION,
    build_grant_suggestions_user_message,
)

logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Controlled error with a safe public message and status code."""

    public_message = "The AI assistant is temporarily unavailable. Please try again later."
    status_code = 503


class AIConfigurationError(AIServiceError):
    public_message = "The AI assistant is not configured for this environment."


class AIGuardrailIntervenedError(AIServiceError):
    public_message = "This request could not be processed by the AI assistant. Please revise the draft and try again."
    status_code = 422


class AIResponseFormatError(AIServiceError):
    public_message = "The AI assistant returned an invalid response. Please try again."
    status_code = 502


class BedrockGrantSuggestionService:
    """IAM-first wrapper around Bedrock Converse for grant-draft suggestions."""

    def __init__(self, config: dict[str, Any], client=None) -> None:
        self._config = config
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        if boto3 is None or BotoConfig is None:
            raise AIConfigurationError("boto3 is not installed.")

        # In ECS, boto3 resolves the task-role credentials automatically.
        self._client = boto3.client(
            "bedrock-runtime",
            region_name=self._config.get("AWS_REGION", "ap-southeast-2"),
            config=BotoConfig(
                connect_timeout=5,
                read_timeout=35,
                retries={"max_attempts": 2, "mode": "standard"},
            ),
        )
        return self._client

    def _guardrail_config(self) -> dict[str, str] | None:
        guardrail_id = self._config.get("AWS_BEDROCK_GUARDRAIL_ID")
        guardrail_version = self._config.get("AWS_BEDROCK_GUARDRAIL_VERSION")
        if bool(guardrail_id) != bool(guardrail_version):
            raise AIConfigurationError(
                "AWS_BEDROCK_GUARDRAIL_ID and AWS_BEDROCK_GUARDRAIL_VERSION must be set together."
            )
        if not guardrail_id:
            return None
        return {
            "guardrailIdentifier": str(guardrail_id),
            "guardrailVersion": str(guardrail_version),
            "trace": "enabled",
        }

    def generate_grant_suggestions(
        self,
        grant_draft: dict[str, Any],
        request_metadata: dict[str, str],
    ) -> tuple[dict[str, Any], dict[str, int | str | None]]:
        model_id = self._config.get("AWS_BEDROCK_MODEL_ID")
        if not model_id:
            raise AIConfigurationError("AWS_BEDROCK_MODEL_ID is not configured.")

        call_args: dict[str, Any] = {
            "modelId": model_id,
            "system": [{"text": GRANT_SUGGESTIONS_SYSTEM_PROMPT}],
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": build_grant_suggestions_user_message(grant_draft)}],
                }
            ],
            "inferenceConfig": {
                "maxTokens": int(self._config.get("AWS_BEDROCK_MAX_TOKENS", 900)),
                "temperature": float(self._config.get("AWS_BEDROCK_TEMPERATURE", 0.2)),
            },
            "requestMetadata": request_metadata,
        }
        guardrail_config = self._guardrail_config()
        if guardrail_config:
            call_args["guardrailConfig"] = guardrail_config

        try:
            response = self._get_client().converse(**call_args)
        except (ClientError, BotoCoreError) as exc:
            logger.warning("Bedrock grant-suggestions call failed: %s", exc.__class__.__name__)
            raise AIServiceError() from exc

        if response.get("stopReason") == "guardrail_intervened":
            logger.info("Bedrock guardrail intervened for grant-suggestions request")
            raise AIGuardrailIntervenedError()

        result = _parse_and_validate_model_response(response)
        usage = response.get("usage", {})
        metrics = response.get("metrics", {})
        metadata: dict[str, int | str | None] = {
            "model_id": str(model_id),
            "prompt_version": PROMPT_VERSION,
            "input_tokens": _as_int_or_none(usage.get("inputTokens")),
            "output_tokens": _as_int_or_none(usage.get("outputTokens")),
            "latency_ms": _as_int_or_none(metrics.get("latencyMs")),
        }
        return result, metadata


def _as_int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_model_text(response: dict[str, Any]) -> str:
    try:
        content = response["output"]["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise AIResponseFormatError() from exc
    text = "".join(block.get("text", "") for block in content if isinstance(block, dict)).strip()
    if not text:
        raise AIResponseFormatError()
    return text


def _strip_code_fence(text: str) -> str:
    fenced = re.fullmatch(r"```(?:json)?\s*(\{.*\})\s*```", text, flags=re.DOTALL)
    return fenced.group(1) if fenced else text


def _truncate_text(value: Any, max_length: int) -> str:
    return value.strip()[:max_length] if isinstance(value, str) else ""


def _parse_and_validate_model_response(response: dict[str, Any]) -> dict[str, Any]:
    try:
        payload = json.loads(_strip_code_fence(_extract_model_text(response)))
    except (TypeError, json.JSONDecodeError) as exc:
        raise AIResponseFormatError() from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("suggestions"), list):
        raise AIResponseFormatError()

    clean_suggestions: list[dict[str, str]] = []
    for item in payload["suggestions"][:MAX_SUGGESTIONS]:
        if not isinstance(item, dict):
            continue
        area = item.get("area")
        priority = item.get("priority")
        suggestion = _truncate_text(item.get("suggestion"), MAX_SUGGESTION_CHARACTERS)
        rationale = _truncate_text(item.get("rationale"), MAX_RATIONALE_CHARACTERS)
        if (
            area in ALLOWED_SUGGESTION_AREAS
            and priority in ALLOWED_PRIORITIES
            and suggestion
            and rationale
        ):
            clean_suggestions.append(
                {
                    "area": area,
                    "priority": priority,
                    "suggestion": suggestion,
                    "rationale": rationale,
                }
            )

    summary = _truncate_text(payload.get("summary"), MAX_SUMMARY_CHARACTERS)
    if not summary:
        summary = "Review the draft against council policy before publishing."
    return {
        "summary": summary,
        "suggestions": clean_suggestions,
        "disclaimer": GRANT_SUGGESTIONS_DISCLAIMER,
    }
