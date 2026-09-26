"""Turnstile-protected public contact and waitlist endpoints.

Public forms are database-first: a verified submission is committed to the
protected platform database before an administrator is notified. Notification
email is deliberately content-free, so email delivery never becomes the system
of record for a person's details or message.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from flask import current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from app import db, limiter
from app.common import email_service
from app.common.encryption import field_encryption_ready
from app.contact import bp
from app.contact.turnstile import TurnstileVerificationError, verify_turnstile_token
from app.models import AuditLog, PublicSubmission

logger = logging.getLogger(__name__)

CONTACT_TYPES = {
    "demo": "Demo enquiry",
    "pricing": "Pricing enquiry",
    "support": "Support enquiry",
    "general": "General enquiry",
}
MAX_LENGTHS = {
    "name": 120,
    "email": 254,
    "organisation": 200,
    "phone": 50,
    "message": 5000,
    "first_name": 80,
}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _json_error(message: str, status: int):
    return jsonify({"error": message}), status


def _client_ip() -> str | None:
    forwarded = request.headers.get("CF-Connecting-IP") or request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",", 1)[0].strip() or request.remote_addr


def _normalise_text(data: dict[str, Any], key: str, *, required: bool = False) -> str:
    value = data.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"{key} must be text.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{key} is required.")
    if len(value) > MAX_LENGTHS[key]:
        raise ValueError(f"{key} is too long.")
    return value


def _audit(action: str, submission_id: int, metadata: dict[str, str]) -> None:
    """Persist request metadata only; never public-form content or email addresses."""
    try:
        db.session.add(
            AuditLog(
                action=action,
                entity_type="public_submission",
                entity_id=submission_id,
                new_values=json.dumps(metadata, sort_keys=True),
                ip_address=_client_ip(),
                user_agent=(request.headers.get("User-Agent") or "")[:500],
            )
        )
        db.session.commit()
    except Exception as exc:  # A stored public submission must never be discarded due to audit failure.
        db.session.rollback()
        logger.error("Unable to write public submission audit record: %s", exc.__class__.__name__)


def _store_submission(
    *,
    submission_type: str,
    contact_type: str | None,
    name: str,
    email: str,
    organisation: str = "",
    phone: str = "",
    message: str = "",
) -> PublicSubmission | None:
    """Commit the protected submission before attempting any notification."""
    if current_app.config.get("PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED", True) and not field_encryption_ready():
        logger.critical("Refusing public submission storage because field encryption is unavailable")
        return None

    submission = PublicSubmission(
        submission_type=submission_type,
        contact_type=contact_type,
        name=name,
        email=email,
        organisation=organisation or None,
        phone=phone or None,
        message=message or None,
        status="new",
        notification_status="pending",
        received_at=datetime.now(timezone.utc),
    )
    try:
        db.session.add(submission)
        db.session.commit()
        return submission
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Unable to store public submission: %s", exc.__class__.__name__)
        return None


def _notify_admin(submission: PublicSubmission) -> str:
    """Send a data-free alert after persistence and record the delivery outcome."""
    recipient = (current_app.config.get("ADMIN_NOTIFICATION_EMAIL") or "").strip()
    dashboard_url = (current_app.config.get("ADMIN_DASHBOARD_URL") or "").strip()
    if not recipient or not dashboard_url:
        status = "not_configured"
        logger.error("Administrator notification routing is not configured")
    else:
        delivered = email_service.send_public_submission_notification(recipient, dashboard_url)
        status = "sent" if delivered else "failed"

    try:
        submission.notification_status = status
        submission.notification_attempted_at = datetime.now(timezone.utc)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.error("Unable to record public submission notification outcome: %s", exc.__class__.__name__)
    return status


def _success_message(submission_type: str) -> str:
    if submission_type == "waitlist":
        return "Thanks — you are on the GrantThrive launch list."
    return "Thanks — your GrantThrive enquiry has been received."


@bp.post("/contact")
@limiter.limit("5 per hour")
def submit_contact_form():
    """Receive a public contact form after mandatory Turnstile validation."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _json_error("A valid form submission is required.", 400)

    expected = {"type", "name", "email", "organisation", "phone", "message", "turnstile_token"}
    unexpected = set(data) - expected
    if unexpected:
        return _json_error("Unsupported form data was submitted.", 400)

    try:
        verify_turnstile_token(data.get("turnstile_token"), _client_ip(), "contact")
        kind = data.get("type", "general")
        if kind not in CONTACT_TYPES:
            raise ValueError("type is not supported.")
        fields = {
            "name": _normalise_text(data, "name", required=True),
            "email": _normalise_text(data, "email", required=True).lower(),
            "organisation": _normalise_text(data, "organisation"),
            "phone": _normalise_text(data, "phone"),
            "message": _normalise_text(data, "message", required=True),
        }
        if not EMAIL_RE.fullmatch(fields["email"]):
            raise ValueError("email is invalid.")
    except TurnstileVerificationError as exc:
        return _json_error(str(exc), 400)
    except ValueError as exc:
        return _json_error(str(exc), 422)

    submission = _store_submission(
        submission_type="contact",
        contact_type=kind,
        **fields,
    )
    if not submission:
        return _json_error("We could not save your message just now. Please try again shortly.", 503)

    notification_status = _notify_admin(submission)
    _audit(
        "public_submission.received",
        submission.id,
        {"form": "contact", "type": kind, "notification": notification_status},
    )
    return jsonify({"message": _success_message("contact")}), 201


@bp.post("/waitlist")
@limiter.limit("5 per hour")
def submit_waitlist_form():
    """Receive a public launch waitlist signup after mandatory Turnstile validation."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _json_error("A valid form submission is required.", 400)

    expected = {"first_name", "email", "turnstile_token"}
    unexpected = set(data) - expected
    if unexpected:
        return _json_error("Unsupported form data was submitted.", 400)

    try:
        verify_turnstile_token(data.get("turnstile_token"), _client_ip(), "waitlist")
        first_name = _normalise_text(data, "first_name", required=True)
        email = _normalise_text(data, "email", required=True).lower()
        if not EMAIL_RE.fullmatch(email):
            raise ValueError("email is invalid.")
    except TurnstileVerificationError as exc:
        return _json_error(str(exc), 400)
    except ValueError as exc:
        return _json_error(str(exc), 422)

    submission = _store_submission(
        submission_type="waitlist",
        contact_type=None,
        name=first_name,
        email=email,
    )
    if not submission:
        return _json_error("We could not save your details just now. Please try again shortly.", 503)

    notification_status = _notify_admin(submission)
    _audit(
        "public_submission.received",
        submission.id,
        {"form": "waitlist", "notification": notification_status},
    )
    return jsonify({"message": _success_message("waitlist")}), 201
