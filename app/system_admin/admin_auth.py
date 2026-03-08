"""
GrantThrive — System Admin Authentication API
==============================================
Dedicated login, logout, token-refresh, and profile endpoints for
GrantThrive staff (system_admin) users.

These endpoints are intentionally separate from the general /auth/login
route so that:
  1. A stricter rate limit can be applied to the admin surface.
  2. The login is hard-restricted to system_admin role only — any other
     role attempting to use this endpoint receives a 403, not a 401,
     to avoid leaking whether the credentials were valid.
  3. Audit logging is more granular (action = "admin_login").
  4. Future MFA or IP-allowlist controls can be applied here without
     affecting the council portal login flow.

Endpoints
---------
POST /api/admin/login          — Authenticate a system_admin user
POST /api/admin/logout         — Log out (audit log + client-side token drop)
POST /api/admin/refresh-token  — Issue a fresh short-lived token
GET  /api/admin/me             — Return the authenticated admin's profile

Security
--------
- Passwords verified with Argon2id (via app.common.password)
- Email lookup uses the AES-256-GCM HMAC index (via app.common.encryption)
- Rate limit: 5 attempts per 10 minutes per IP (stricter than portal login)
- Constant-time dummy check on unknown email to prevent user enumeration
- All login events (success and failure) written to audit_log
- Tokens are short-lived: 8 hours (vs 7 days for portal tokens)
- Rehash-on-login: legacy PBKDF2 hashes are silently upgraded to Argon2id

Domain: admin.grantthrive.com
"""

import logging
from datetime import datetime, timedelta, timezone

import jwt
from flask import request, jsonify, current_app

from app import db, limiter
from app.auth.routes import (
    _generate_token,
    _decode_token,
    _write_audit_log,
    token_required,
)
from app.common.encryption import hmac_index
from app.common.password import hash_password, verify_password
from app.models import User
from app.system_admin import bp

logger = logging.getLogger(__name__)

# ── Admin-specific JWT settings ───────────────────────────────────────────────
ADMIN_JWT_EXPIRY_HOURS = 8   # Shorter-lived than portal tokens (7 days)


def _generate_admin_token(user: User) -> str:
    """Issue a short-lived JWT for a system_admin user."""
    payload = {
        "sub":        str(user.id),
        "email":      user.email,
        "role":       user.role,
        "council_id": None,   # system_admin has no council scope
        "iat":        datetime.now(timezone.utc),
        "exp":        datetime.now(timezone.utc) + timedelta(hours=ADMIN_JWT_EXPIRY_HOURS),
        "scope":      "admin",  # Distinguishes admin tokens from portal tokens
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256",
    )


def _admin_token_required(f):
    """Decorator: require a valid admin-scoped JWT (role == system_admin)."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        # Enforce admin scope — reject portal tokens used against admin endpoints
        if payload.get("role") != "system_admin":
            return jsonify({"error": "Admin access required."}), 403

        user = db.session.get(User, int(payload["sub"]))
        if not user or not user.is_active or user.role != "system_admin":
            return jsonify({"error": "Admin account not found or inactive."}), 401

        return f(user, *args, **kwargs)

    return decorated


# ── Helpers ───────────────────────────────────────────────────────────────────

def _admin_profile(user: User) -> dict:
    """Serialise a system_admin User to a safe response dict."""
    return {
        "id":         user.id,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "full_name":  f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "role":       user.role,
        "is_active":  user.is_active,
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _lookup_admin_by_email(email: str) -> User | None:
    """Look up a system_admin user by email using the HMAC index.

    Falls back to plaintext lookup if HMAC index is not configured
    (development environments without encryption keys set).
    """
    email_hash = hmac_index(email)
    if email_hash:
        return User.query.filter_by(
            email_hmac=email_hash,
            role="system_admin",
        ).first()
    # Fallback: plaintext lookup (development only — logs a warning)
    logger.warning(
        "HMAC index not available — falling back to plaintext email lookup. "
        "Set FIELD_HMAC_KEY in production."
    )
    return User.query.filter_by(email=email, role="system_admin").first()


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/admin/login", methods=["POST"])
@limiter.limit(
    "5 per 10 minutes",
    error_message="Too many admin login attempts. Please try again in 10 minutes.",
)
def admin_login():
    """
    Authenticate a GrantThrive staff (system_admin) user.

    Stricter than the portal login:
      - Only system_admin role is accepted; other roles receive 403.
      - Rate limit: 5 attempts per 10 minutes (vs 10 per 15 min for portal).
      - Token expiry: 8 hours (vs 7 days for portal).
      - All attempts (success and failure) are audit-logged.

    Request body:
        { "email": "staff@grantthrive.com", "password": "..." }

    Response (200):
        {
            "token": "<jwt>",
            "expires_in": 28800,
            "user": { "id": ..., "email": ..., "role": "system_admin", ... }
        }

    Errors:
        400 — Missing email or password
        401 — Invalid credentials
        403 — Account is not a system_admin (credentials may be valid but role is wrong)
        429 — Rate limit exceeded
    """
    data     = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    # Look up via HMAC index (encrypted email lookup)
    user = _lookup_admin_by_email(email)

    if not user:
        # Constant-time dummy check — prevents user enumeration via timing
        verify_password(
            '$argon2id$v=19$m=65536,t=3,p=4$dummysaltdummysalt$dummyhashvaluedummyhashvalue',
            password,
        )
        logger.warning("Admin login: unknown email attempted: %s", email)
        _write_audit_log(
            user_id=0,
            action="admin_login_failed",
            details=f"Unknown email: {email}",
        )
        return jsonify({"error": "Invalid email or password."}), 401

    # Verify password (Argon2id + legacy PBKDF2 fallback)
    is_valid, needs_rehash = verify_password(user.password_hash, password)

    if not is_valid:
        logger.warning("Admin login: invalid password for user_id=%d", user.id)
        _write_audit_log(
            user_id=user.id,
            action="admin_login_failed",
            details="Invalid password",
        )
        return jsonify({"error": "Invalid email or password."}), 401

    # Role guard — credentials may be valid but the account is not system_admin
    if user.role != "system_admin":
        logger.warning(
            "Admin login: user_id=%d has role=%s, not system_admin",
            user.id, user.role,
        )
        _write_audit_log(
            user_id=user.id,
            action="admin_login_denied",
            details=f"Role mismatch: {user.role}",
        )
        return jsonify({"error": "This endpoint is for GrantThrive staff only."}), 403

    # Account active check
    if not user.is_active:
        _write_audit_log(
            user_id=user.id,
            action="admin_login_denied",
            details="Account inactive",
        )
        return jsonify({"error": "Your admin account has been deactivated."}), 403

    # Transparently rehash legacy or outdated hashes
    if needs_rehash:
        user.password_hash = hash_password(password)
        logger.info("Admin login: rehashed password for user_id=%d to Argon2id", user.id)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = _generate_admin_token(user)

    logger.info("Admin login: success for user_id=%d", user.id)
    _write_audit_log(
        user_id=user.id,
        action="admin_login",
        details="Successful admin login",
    )

    return jsonify({
        "token":      token,
        "expires_in": ADMIN_JWT_EXPIRY_HOURS * 3600,
        "user":       _admin_profile(user),
    }), 200


@bp.route("/admin/logout", methods=["POST"])
@_admin_token_required
def admin_logout(current_user: User):
    """
    Log out the authenticated admin user.

    Tokens are stateless JWTs — the client must drop the token.
    This endpoint exists to write an audit log entry and allow
    future server-side token revocation (e.g. a deny-list) to be
    added without changing the client interface.

    Response (200):
        { "message": "Logged out successfully." }
    """
    _write_audit_log(
        user_id=current_user.id,
        action="admin_logout",
        details="Admin logout",
    )
    logger.info("Admin logout: user_id=%d", current_user.id)
    return jsonify({"message": "Logged out successfully."}), 200


@bp.route("/admin/refresh-token", methods=["POST"])
@_admin_token_required
def admin_refresh_token(current_user: User):
    """
    Issue a fresh 8-hour admin token for the authenticated user.

    The client should call this before the current token expires to
    maintain a seamless session without requiring re-authentication.

    Response (200):
        { "token": "<new_jwt>", "expires_in": 28800 }
    """
    new_token = _generate_admin_token(current_user)
    _write_audit_log(
        user_id=current_user.id,
        action="admin_token_refresh",
        details="Token refreshed",
    )
    return jsonify({
        "token":      new_token,
        "expires_in": ADMIN_JWT_EXPIRY_HOURS * 3600,
    }), 200


@bp.route("/admin/me", methods=["GET"])
@_admin_token_required
def admin_me(current_user: User):
    """
    Return the authenticated admin's profile.

    Useful for the frontend to confirm the session is still valid
    and to populate the admin dashboard header.

    Response (200):
        { "user": { ... } }
    """
    return jsonify({"user": _admin_profile(current_user)}), 200
