"""Advisory-only AI endpoints for authorised council users."""

from __future__ import annotations

import json
import logging
from decimal import Decimal
from typing import Any

from flask import current_app, jsonify, request

from app import db, limiter
from app.ai import bp
from app.ai.prompts import MAX_DRAFT_CHARACTERS
from app.ai.service import (
    AIConfigurationError,
    AIGuardrailIntervenedError,
    AIServiceError,
    BedrockGrantSuggestionService,
)
from app.common.permissions import permission_required
from app.models import AuditLog, Council

logger = logging.getLogger(__name__)

_MAX_LIST_ITEMS = 12
_MAX_LIST_ITEM_LENGTH = 500
_TEXT_FIELD_LIMITS = {
    "title": 200,
    "description": 6000,
    "category": 100,
    "opens_at": 50,
    "closes_at": 50,
    "assessment_deadline": 50,
    "notification_date": 50,
    "community_engagement_approach": 1000,
    "location_name": 200,
    "state": 50,
    "region": 100,
}
_LIST_FIELDS = {"eligibility_criteria", "assessment_criteria", "required_documents"}
_BOOLEAN_FIELDS = {
    "allow_multiple_applications",
    "require_community_voting",
    "enable_mapping",
}
_NUMBER_FIELDS = {
    "total_budget",
    "min_amount_per_application",
    "max_amount_per_application",
}
_ALLOWED_DRAFT_FIELDS = set(_TEXT_FIELD_LIMITS) | _LIST_FIELDS | _BOOLEAN_FIELDS | _NUMBER_FIELDS
_ALLOWED_REQUEST_FIELDS = {"grant_draft", "council_id"}


def _validation_error(message: str):
    return jsonify({"error": message}), 400


def _safe_text(value: Any, field: str, max_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string.")
    clean = value.strip()
    if len(clean) > max_length:
        raise ValueError(f"{field} must not exceed {max_length} characters.")
    return clean


def _safe_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings.")
    if len(value) > _MAX_LIST_ITEMS:
        raise ValueError(f"{field} must contain no more than {_MAX_LIST_ITEMS} items.")
    clean: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field} must contain strings only.")
        item = item.strip()
        if len(item) > _MAX_LIST_ITEM_LENGTH:
            raise ValueError(f"Each {field} item must not exceed {_MAX_LIST_ITEM_LENGTH} characters.")
        if item:
            clean.append(item)
    return clean


def _safe_number(value: Any, field: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal, str)):
        raise ValueError(f"{field} must be a number.")
    try:
        result = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{field} must be a valid number.") from exc
    if result < 0 or result > Decimal("999999999999"):
        raise ValueError(f"{field} is outside the supported range.")
    return format(result, "f")


def _validate_grant_draft(raw_draft: Any) -> dict[str, Any]:
    """Whitelist and bound a non-applicant grant-program draft."""
    if not isinstance(raw_draft, dict):
        raise ValueError("grant_draft must be a JSON object.")
    unexpected = set(raw_draft) - _ALLOWED_DRAFT_FIELDS
    if unexpected:
        raise ValueError(f"Unsupported grant_draft field(s): {', '.join(sorted(unexpected))}.")

    clean: dict[str, Any] = {}
    for field, max_length in _TEXT_FIELD_LIMITS.items():
        if field in raw_draft:
            clean[field] = _safe_text(raw_draft[field], field, max_length)
    for field in _LIST_FIELDS:
        if field in raw_draft:
            clean[field] = _safe_list(raw_draft[field], field)
    for field in _BOOLEAN_FIELDS:
        if field in raw_draft:
            if not isinstance(raw_draft[field], bool):
                raise ValueError(f"{field} must be a boolean.")
            clean[field] = raw_draft[field]
    for field in _NUMBER_FIELDS:
        if field in raw_draft and raw_draft[field] is not None:
            clean[field] = _safe_number(raw_draft[field], field)

    if not any(clean.get(field) for field in ("title", "description", "category")):
        raise ValueError("Provide at least one of title, description, or category.")
    if len(json.dumps(clean, ensure_ascii=False)) > MAX_DRAFT_CHARACTERS:
        raise ValueError("grant_draft is too large to process.")
    return clean


def _resolve_council_id(current_user, data: dict[str, Any]) -> int:
    if current_user.role == "system_admin":
        council_id = data.get("council_id")
        if not isinstance(council_id, int) or isinstance(council_id, bool):
            raise ValueError("council_id is required for system_admin.")
    else:
        council_id = current_user.council_id
        if not council_id:
            raise ValueError("Your account is not linked to a council.")
    if not db.session.get(Council, council_id):
        raise LookupError("Council not found.")
    return council_id


def _write_audit_metadata(current_user, council_id: int, metadata: dict[str, Any], count: int) -> None:
    """Record metadata only; never persist raw prompts or model output."""
    record = AuditLog(
        user_id=current_user.id,
        council_id=council_id,
        action="ai_grant_suggestions_generated",
        entity_type="ai_grant_suggestions",
        entity_id=council_id,
        new_values=json.dumps({**metadata, "suggestion_count": count, "feature": "grant_suggestions"}, sort_keys=True),
        ip_address=request.remote_addr,
        user_agent=(request.user_agent.string or "")[:500],
    )
    try:
        db.session.add(record)
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Unable to write AI usage audit metadata")


@bp.post("/grant-suggestions")
@limiter.limit("20 per hour")
@permission_required("ai:grant_suggestions")
def grant_suggestions(current_user):
    """Generate advisory suggestions for a validated grant-program draft."""
    if not current_app.config.get("AI_FEATURES_ENABLED", False):
        return jsonify({"error": "The AI assistant is not enabled for this environment."}), 503
    if not request.is_json:
        return _validation_error("Content-Type must be application/json.")

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _validation_error("A JSON object is required.")
    unexpected = set(data) - _ALLOWED_REQUEST_FIELDS
    if unexpected:
        return _validation_error(f"Unsupported request field(s): {', '.join(sorted(unexpected))}.")

    try:
        council_id = _resolve_council_id(current_user, data)
        grant_draft = _validate_grant_draft(data.get("grant_draft"))
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    except ValueError as exc:
        return _validation_error(str(exc))

    request_metadata = {
        "feature": "grant_suggestions",
        "user_id": str(current_user.id),
        "council_id": str(council_id),
    }
    try:
        result, metadata = BedrockGrantSuggestionService(current_app.config).generate_grant_suggestions(
            grant_draft,
            request_metadata,
        )
    except AIGuardrailIntervenedError as exc:
        return jsonify({"error": exc.public_message}), exc.status_code
    except AIConfigurationError as exc:
        logger.warning("AI grant suggestions configuration error")
        return jsonify({"error": exc.public_message}), exc.status_code
    except AIServiceError as exc:
        return jsonify({"error": exc.public_message}), exc.status_code

    _write_audit_metadata(current_user, council_id, metadata, len(result["suggestions"]))
    return jsonify(
        {
            **result,
            "metadata": {
                "prompt_version": metadata["prompt_version"],
                "advisory_only": True,
            },
        }
    ), 200
