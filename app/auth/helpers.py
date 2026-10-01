"""
GrantThrive — Auth Helpers
===========================
Shared utilities and serialisers used by all auth route modules.
Import from here rather than from routes.py to avoid circular dependencies.
"""
import jwt
import logging
from datetime import datetime, timedelta, timezone
from flask import request, current_app

from app.common.encryption import hmac_index
from app import db
from app.models import User, Council

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
JWT_ADMIN_EXPIRY_HRS = 2
JWT_ADMIN_REFRESH_MINS = 15


# ── Date/time helpers ─────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_dt(dt) -> datetime | None:
    """Ensure a datetime is timezone-aware (UTC). Returns None if dt is None."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# ── User lookup ───────────────────────────────────────────────────────────────

def _find_user_by_email(email: str) -> User | None:
    """
    Look up a User by email address.
    Email is stored encrypted; we use the HMAC index for the lookup.
    Returns None if not found.
    """
    idx = hmac_index(email.lower())
    return User.query.filter_by(email_hmac=idx).first()


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _generate_token(user: User) -> str:
    council_id = user.council_id
    council_subdomain = None
    if council_id:
        council = db.session.get(Council, council_id)
        if council:
            council_subdomain = council.subdomain
    now = _utcnow()
    expiry = (
        now + timedelta(hours=JWT_ADMIN_EXPIRY_HRS)
        if user.role == "system_admin"
        else now + timedelta(days=JWT_EXPIRY_DAYS)
    )
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "council_id": council_id,
        "council_subdomain": council_subdomain,
        "iat": now,
        "exp": expiry,
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=JWT_ALGORITHM,
    )


def _decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
    )


# ── Serialiser ────────────────────────────────────────────────────────────────

def _user_to_dict(user: User) -> dict:
    council_data = None
    if user.council_id:
        council = db.session.get(Council, user.council_id)
        if council:
            council_data = {
                "id": council.id,
                "name": council.name,
                "subdomain": council.subdomain,
                "slug": council.slug,
                "logo_url": getattr(council, "logo_url", None),
                "primary_colour": getattr(council, "primary_colour", None),
                "secondary_colour": getattr(council, "secondary_colour", None),
                "portal_url": council.portal_url() if hasattr(council, "portal_url") else None,
            }
    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "role": user.role,
        "council_id": user.council_id,
        "council": council_data,
        "is_active": user.is_active,
        "is_approved": user.is_approved,
        "phone": getattr(user, "phone", None),
        "organisation": getattr(user, "organisation", None),
        "organization_name": getattr(user, "organisation", None),
        "abn": getattr(user, "abn", None),
        "position": getattr(user, "position", None),
        "department": getattr(user, "department", None),
        "subdomain": getattr(user, "requested_subdomain", None),
        "created_at": user.created_at.isoformat() if getattr(user, "created_at", None) else None,
        "last_login": user.last_login.isoformat() if getattr(user, "last_login", None) else None,
    }


# ── Audit log ─────────────────────────────────────────────────────────────────

def _write_audit_log(
    user_id: int,
    action: str,
    details: str | None,
    council_id: int | None = None,
) -> None:
    from app.models import AuditLog
    try:
        forwarded = request.environ.get("HTTP_X_FORWARDED_FOR")
        ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else request.environ.get("REMOTE_ADDR", "unknown")
        )
        log = AuditLog(
            user_id=user_id,
            council_id=council_id,
            action=action,
            entity_type="auth",
            entity_id=user_id,
            new_values=details,
            ip_address=ip,
            user_agent=request.headers.get("User-Agent", ""),
            created_at=_utcnow(),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning("Failed to write audit log for action '%s': %s", action, exc)
