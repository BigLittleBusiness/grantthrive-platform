"""Turnstile-protected public contact and waitlist endpoints.

This module is intentionally separate from council and applicant communications:
it receives only messages intended for the GrantThrive team. It neither exposes
nor accepts a public destination email address.
"""

from __future__ import annotations

import html
import json
import logging
import re
from typing import Any

from flask import current_app, jsonify, request

from app import db, limiter
from app.common import email_service
from app.contact import bp
from app.contact.turnstile import TurnstileVerificationError, verify_turnstile_token
from app.models import AuditLog

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


def _audit(action: str, metadata: dict[str, str]) -> None:
    """Persist safe request metadata only; never form contents or email addresses."""
    try:
        db.session.add(
            AuditLog(
                action=action,
                entity_type="public_contact",
                entity_id=0,
                new_values=json.dumps(metadata, sort_keys=True),
                ip_address=_client_ip(),
                user_agent=(request.headers.get("User-Agent") or "")[:500],
            )
        )
        db.session.commit()
    except Exception as exc:  # Contact delivery should not be silently lost to an audit issue.
        db.session.rollback()
        logger.error("Unable to write public contact audit record: %s", exc.__class__.__name__)


def _send_contact_email(kind: str, fields: dict[str, str]) -> bool:
    recipient = current_app.config.get("CONTACT_INBOX_EMAIL", "").strip()
    if not recipient:
        logger.error("CONTACT_INBOX_EMAIL is not configured")
        return False

    subject = f"GrantThrive - {CONTACT_TYPES[kind]}"
    details = [
        ("Name", fields["name"]),
        ("Email", fields["email"]),
        ("Council / organisation", fields["organisation"] or "Not supplied"),
        ("Phone", fields["phone"] or "Not supplied"),
    ]
    details_html = "".join(
        f"<p><strong>{html.escape(label)}:</strong> {html.escape(value)}</p>" for label, value in details
    )
    text_details = "\n".join(f"{label}: {value}" for label, value in details)
    html_body = f"""
<h2>New GrantThrive {html.escape(CONTACT_TYPES[kind].lower())}</h2>
<div class="info-box">{details_html}</div>
<h3>Message</h3>
<p>{html.escape(fields['message']).replace(chr(10), '<br>')}</p>
"""
    text_body = f"New GrantThrive {CONTACT_TYPES[kind].lower()}\n\n{text_details}\n\nMessage:\n{fields['message']}"
    return email_service.send_email(recipient, subject, html_body, text_body, reply_to=fields["email"])


def _send_waitlist_email(first_name: str, email: str) -> bool:
    recipient = current_app.config.get("CONTACT_INBOX_EMAIL", "").strip()
    if not recipient:
        logger.error("CONTACT_INBOX_EMAIL is not configured")
        return False

    subject = "GrantThrive - Waitlist signup"
    html_body = f"""
<h2>New GrantThrive waitlist signup</h2>
<div class="info-box">
  <p><strong>First name:</strong> {html.escape(first_name)}</p>
  <p><strong>Email:</strong> {html.escape(email)}</p>
</div>
"""
    text_body = f"New GrantThrive waitlist signup\n\nFirst name: {first_name}\nEmail: {email}"
    return email_service.send_email(recipient, subject, html_body, text_body, reply_to=email)


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

    delivered = _send_contact_email(kind, fields)
    _audit("public_contact.submitted", {"form": "contact", "type": kind, "delivery": "sent" if delivered else "failed"})
    if not delivered:
        return _json_error("We could not send your message just now. Please try again shortly.", 503)

    return jsonify({"message": "Thanks — your GrantThrive enquiry has been sent."}), 201


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

    delivered = _send_waitlist_email(first_name, email)
    _audit("public_contact.submitted", {"form": "waitlist", "delivery": "sent" if delivered else "failed"})
    if not delivered:
        return _json_error("We could not save your details just now. Please try again shortly.", 503)

    return jsonify({"message": "Thanks — you are on the GrantThrive launch list."}), 201
