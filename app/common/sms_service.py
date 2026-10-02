"""
GrantThrive — Centralised Twilio SMS Service
=============================================
GrantThrive operates a single Twilio account.  Councils do NOT manage their
own Twilio credentials — SMS is delivered on their behalf through GrantThrive's
account, and usage is tracked per council for billing purposes.

Credentials are managed by a system admin on the Twilio configuration page
(Admin Dashboard → SMS) and stored in SystemConfig — the auth token encrypted
with SYSTEM_CONFIG_ENCRYPTION_KEY. Sending is skipped (logged instead) until
the integration is enabled there with an Account SID, Auth Token and either a
Messaging Service SID or a From number.

All public functions return a (success: bool, message: str) tuple so callers
can log failures without crashing the notification pipeline.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Twilio client (credentials from SystemConfig) ─────────────────────────────

def _get_client():
    """Return (Twilio client, sender kwargs), or (None, None) when SMS is not configured."""
    from app.models import SystemConfig

    if SystemConfig.get("twilio_enabled") != "true":
        return None, None
    account_sid = SystemConfig.get("twilio_account_sid")
    auth_token = SystemConfig.get("twilio_auth_token")
    messaging_sid = SystemConfig.get("twilio_messaging_service_sid")
    from_number = SystemConfig.get("twilio_from_number")
    if not (account_sid and auth_token and (messaging_sid or from_number)):
        logger.warning("Twilio is enabled but its credentials are incomplete; SMS will be logged, not sent.")
        return None, None

    from twilio.rest import Client  # type: ignore
    sender = {"messaging_service_sid": messaging_sid} if messaging_sid else {"from_": from_number}
    return Client(account_sid, auth_token), sender


# ── Core send function ────────────────────────────────────────────────────────

def send_sms(to_phone: str, body: str, council_id: int | None = None) -> tuple[bool, str]:
    """
    Send a single SMS via Twilio.

    Args:
        to_phone:   Recipient phone number in E.164 format, e.g. "+61412345678".
        body:       Message text (max 160 chars for a single segment).
        council_id: Optional council ID for usage tracking / audit logging.

    Returns:
        (True, twilio_message_sid) on success.
        (False, error_message) on failure.
    """
    if not to_phone or not to_phone.startswith("+"):
        return False, f"Invalid phone number format: {to_phone!r} (must be E.164)"

    client, sender = _get_client()

    # ── Not configured (development / test): log instead of sending ──────────
    if not client:
        logger.info(
            "[SMS-DEV] Would send to=%s council=%s body=%r",
            to_phone, council_id, body
        )
        return True, "dev-mode-not-sent"

    try:
        message = client.messages.create(body=body, to=to_phone, **sender)

        logger.info(
            "SMS sent sid=%s to=%s council=%s status=%s",
            message.sid, to_phone, council_id, message.status
        )

        # ── Track usage per council ───────────────────────────────────────────
        if council_id:
            _record_usage(council_id, message.sid)

        return True, message.sid

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "SMS send failed to=%s council=%s error=%s",
            to_phone, council_id, exc
        )
        return False, str(exc)


# ── Usage tracking ────────────────────────────────────────────────────────────

def _record_usage(council_id: int, message_sid: str) -> None:
    """Increment the council's SMS usage counter in the database."""
    try:
        from app import db  # local import to avoid circular dependency
        from app.models import CouncilSmsUsage

        today = datetime.now(timezone.utc).date()
        record = CouncilSmsUsage.query.filter_by(
            council_id=council_id, date=today
        ).first()

        if record:
            record.messages_sent += 1
        else:
            record = CouncilSmsUsage(
                council_id=council_id,
                date=today,
                messages_sent=1,
            )
            db.session.add(record)

        db.session.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not record SMS usage for council %s: %s", council_id, exc)


# ── Notification helpers ──────────────────────────────────────────────────────

def send_application_received(
    to_phone: str, first_name: str, grant_title: str,
    council_name: str, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, your application for '{grant_title}' at "
        f"{council_name} has been received. We'll be in touch soon. "
        f"— GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_application_approved(
    to_phone: str, first_name: str, grant_title: str,
    council_name: str, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Great news {first_name}! Your application for '{grant_title}' "
        f"at {council_name} has been APPROVED. Check your email for details. "
        f"— GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_application_rejected(
    to_phone: str, first_name: str, grant_title: str,
    council_name: str, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, your application for '{grant_title}' at "
        f"{council_name} was unsuccessful. Check your email for feedback. "
        f"— GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_deadline_reminder(
    to_phone: str, first_name: str, grant_title: str,
    days_remaining: int, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, reminder: '{grant_title}' closes in "
        f"{days_remaining} day{'s' if days_remaining != 1 else ''}. "
        f"Log in to GrantThrive to complete your application. — GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_document_required(
    to_phone: str, first_name: str, grant_title: str,
    council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, additional documents are required for your "
        f"'{grant_title}' application. Please log in to GrantThrive to upload them. "
        f"— GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_payment_processed(
    to_phone: str, first_name: str, amount_aud: float,
    grant_title: str, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, a payment of ${amount_aud:,.2f} AUD has been "
        f"processed for your '{grant_title}' grant. — GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)


def send_voting_reminder(
    to_phone: str, first_name: str, session_title: str,
    hours_remaining: int, council_id: int | None = None
) -> tuple[bool, str]:
    body = (
        f"Hi {first_name}, community voting for '{session_title}' closes in "
        f"{hours_remaining} hour{'s' if hours_remaining != 1 else ''}. "
        f"Log in to GrantThrive to cast your vote. — GrantThrive"
    )
    return send_sms(to_phone, body[:160], council_id)
