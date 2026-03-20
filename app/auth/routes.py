"""
GrantThrive — Authentication Routes
=====================================
Provides JWT-based authentication endpoints consumed by all GrantThrive UI apps
via the shared @grantthrive/auth library.

Multi-tenancy
-------------
The JWT payload now includes ``council_id`` and ``council_subdomain`` so that
every frontend app can identify the tenant without an extra API call.

  system_admin users have council_id = null in the JWT (they span all tenants).
  All other roles have council_id = <their council's id>.

Endpoints:
  POST /auth/login          — Email + password login; returns JWT + user profile
  POST /auth/logout         — Invalidate token (client-side; server logs the event)
  POST /auth/register       — New user registration (scoped to current tenant)
  POST /auth/verify-token   — Validate a JWT and return the current user profile
  POST /auth/demo-login     — Demo login for development/testing environments
  POST /auth/change-password — Change authenticated user's password

Domain: grantthrive.com
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify, current_app, g
from app.common.password import hash_password, verify_password
from app.common.encryption import hmac_index

from app import db, limiter
from app.auth import bp
from app.models import User, Council

logger = logging.getLogger(__name__)

# ── JWT helpers ───────────────────────────────────────────────────────────────

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
JWT_ADMIN_EXPIRY_HRS = 2
JWT_ADMIN_REFRESH_MINS = 15


def _generate_token(user: User) -> str:
    """Issue a signed JWT for the given user, embedding council context."""
    council_id = user.council_id
    council_subdomain = None
    if council_id:
        council = db.session.get(Council, council_id)
        if council:
            council_subdomain = council.subdomain

    now = datetime.now(timezone.utc)
    if user.role == "system_admin":
        expiry = now + timedelta(hours=JWT_ADMIN_EXPIRY_HRS)
    else:
        expiry = now + timedelta(days=JWT_EXPIRY_DAYS)

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
    """Decode and validate a JWT. Returns the payload dict or raises."""
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
    )


def _user_to_dict(user: User) -> dict:
    """Serialise a User record to a safe dict for API responses."""
    council_data = None
    if user.council_id:
        council = db.session.get(Council, user.council_id)
        if council:
            council_data = {
                "id": council.id,
                "name": council.name,
                "subdomain": council.subdomain,
                "slug": council.slug,
                "logo_url": council.logo_url,
                "primary_colour": council.primary_colour,
                "secondary_colour": council.secondary_colour,
                "portal_url": council.portal_url(),
            }

    return {
        "id": user.id,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": f"{user.first_name} {user.last_name}",
        "role": user.role,
        "council_id": user.council_id,
        "council": council_data,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def token_required(f):
    """Decorator: require a valid JWT in the Authorization header."""
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

        user = db.session.get(User, int(payload["sub"]))
        if not user or not user.is_active:
            return jsonify({"error": "User account not found or inactive."}), 401

        return f(user, *args, **kwargs)

    return decorated


def role_required(*roles):
    """Decorator: require the authenticated user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return f(current_user, *args, **kwargs)

        return decorated

    return decorator


# ── Audit logging helper ──────────────────────────────────────────────────────

def _write_audit_log(
    user_id: int,
    action: str,
    details: str | None,
    council_id: int | None = None,
) -> None:
    """Write a row to the audit_logs table. Silently swallows errors."""
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
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        logger.warning("Failed to write audit log for action '%s': %s", action, exc)


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/login", methods=["POST"])
@limiter.limit(
    "10 per 15 minutes",
    error_message="Too many login attempts from this IP. Please try again in 15 minutes.",
)
def login():
    """
    Authenticate a user with email and password.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    email_digest = hmac_index(email)
    user = User.query.filter_by(email_hmac=email_digest).first()

    if not user:
        logger.warning("Failed login attempt for email: %s", email)
        return jsonify({"error": "Invalid email or password."}), 401

    is_valid, needs_rehash = verify_password(user.password_hash, password)
    if not is_valid:
        logger.warning("Failed login attempt for user_id=%d", user.id)
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"error": "Your account is pending approval or has been suspended."}), 403

    current_council = getattr(g, "council", None)
    if current_council and user.role != "system_admin":
        if user.council_id != current_council.id:
            logger.warning(
                "Cross-tenant login attempt: user_id=%d (council_id=%s) "
                "tried to log in via subdomain=%s (council_id=%d)",
                user.id, user.council_id, current_council.subdomain, current_council.id,
            )
            return jsonify({"error": "Invalid email or password."}), 401

    if needs_rehash:
        user.password_hash = hash_password(password)
        logger.info("Rehashed password for user_id=%d to Argon2id", user.id)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = _generate_token(user)
    logger.info(
        "Successful login: user_id=%d role=%s council_id=%s",
        user.id, user.role, user.council_id,
    )
    _write_audit_log(user.id, "login", f"role={user.role}", council_id=user.council_id)

    return jsonify({
        "token": token,
        "user": _user_to_dict(user),
    }), 200


@bp.route("/logout", methods=["POST"])
def logout():
    """
    Log out the current user.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
            user_id = int(payload.get("sub", 0))
            council_id = payload.get("council_id")
            logger.info("Logout: user_id=%s", user_id)
            _write_audit_log(user_id, "logout", None, council_id=council_id)
        except jwt.InvalidTokenError:
            pass
    return jsonify({"message": "Logged out successfully."}), 200


@bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    role = data.get("role") or data.get("user_type") or "community_member"
    organisation = (data.get("organisation") or "").strip() or None
    abn = (data.get("abn") or "").strip() or None
    email_opt_in = bool(data.get("email_opt_in", True))

    if not all([email, password, first_name, last_name]):
        return jsonify({"error": "Email, password, first name, and last name are required."}), 400

    allowed_roles = {"community_member", "professional_consultant"}
    if role not in allowed_roles:
        role = "community_member"

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    email_digest = hmac_index(email)
    if User.query.filter_by(email_hmac=email_digest).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    current_council = getattr(g, "council", None)
    council_id = current_council.id if current_council else None

    base_username = email.split("@")[0]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        council_id=council_id,
        is_active=False,
        is_approved=False,
        organisation=organisation,
        abn=abn,
        email_opt_in=email_opt_in,
    )
    user.set_email(email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    logger.info(
        "New registration: user_id=%d email=%s role=%s council_id=%s (pending approval)",
        user.id, email, role, council_id,
    )
    _write_audit_log(user.id, "register", f"email={email} role={role}", council_id=council_id)

    try:
        from app.common.notifications import notify
        from app.common import email_service

        notify(
            user_id=user.id,
            ntype="registration_confirmed",
            title="Welcome to GrantThrive",
            message="Your account has been created and is pending approval.",
            link="portal/community/dashboard",
            send_email_fn=lambda: email_service.send_registration_confirmation(email, first_name),
        )
    except Exception as _ne:
        logger.warning("Registration notification failed: %s", _ne)

    return jsonify({
        "message": "Registration successful. Your account is pending approval.",
        "user": _user_to_dict(user),
        "requires_approval": True,
    }), 201


@bp.route("/verify-token", methods=["POST"])
def verify_token():
    """
    Validate a JWT and return the current user profile.
    """
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""

    auth_header = request.headers.get("Authorization", "")
    if not token and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    if not token:
        return jsonify({"valid": False, "error": "No token provided."}), 401

    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token has expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token."}), 401

    user = db.session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return jsonify({"valid": False, "error": "User not found or inactive."}), 401

    response_body = {
        "valid": True,
        "user": _user_to_dict(user),
    }

    if user.role == "system_admin":
        exp_ts = payload.get("exp", 0)
        now_ts = datetime.now(timezone.utc).timestamp()
        remaining_mins = (exp_ts - now_ts) / 60
        if remaining_mins < JWT_ADMIN_REFRESH_MINS:
            response_body["new_token"] = _generate_token(user)

    return jsonify(response_body), 200


@bp.route("/demo-login", methods=["POST"])
def demo_login():
    """
    Demo login for development/testing environments.
    """
    if (
        current_app.config.get("ENV") == "production"
        or (
            not current_app.config.get("TESTING")
            and current_app.config.get("FLASK_ENV") == "production"
        )
    ):
        return jsonify({"error": "Demo login is not available in production."}), 403

    data = request.get_json(silent=True) or {}
    demo_type = data.get("demo_type", "council_admin")

    demo_council = Council.query.filter_by(subdomain="demo").first()
    if not demo_council:
        demo_council = Council(
            name="Demo Council",
            subdomain="demo",
            slug="demo-council",
            state="VIC",
            plan="professional",
            is_active=True,
            contact_email="demo@grantthrive.com",
        )
        db.session.add(demo_council)
        db.session.flush()

    demo_users = {
        "council_admin": {
            "email": "demo.admin@melbourne.vic.gov.au",
            "first_name": "Demo",
            "last_name": "Council Admin",
            "role": "council_admin",
            "council_id": demo_council.id,
        },
        "council_staff": {
            "email": "demo.staff@melbourne.vic.gov.au",
            "first_name": "Demo",
            "last_name": "Council Staff",
            "role": "council_staff",
            "council_id": demo_council.id,
        },
        "community_member": {
            "email": "demo.community@example.com",
            "first_name": "Demo",
            "last_name": "Community Member",
            "role": "community_member",
            "council_id": demo_council.id,
        },
        "professional_consultant": {
            "email": "demo.consultant@grantsuccess.com",
            "first_name": "Demo",
            "last_name": "Consultant",
            "role": "professional_consultant",
            "council_id": None,
        },
        "system_admin": {
            "email": "demo.sysadmin@grantthrive.com",
            "first_name": "Demo",
            "last_name": "System Admin",
            "role": "system_admin",
            "council_id": None,
        },
    }

    profile = demo_users.get(demo_type, demo_users["council_admin"])
    email_digest = hmac_index(profile["email"].strip().lower())

    user = User.query.filter_by(email_hmac=email_digest).first()
    if not user:
        base_username = profile["email"].split("@")[0].replace(".", "_")
        user = User(
            username=base_username,
            first_name=profile["first_name"],
            last_name=profile["last_name"],
            role=profile["role"],
            council_id=profile["council_id"],
            is_active=True,
            is_approved=True,
        )
        user.set_email(profile["email"])
        user.set_password("demo_password_not_for_production")
        db.session.add(user)

    user.last_login = datetime.now(timezone.utc)
    db.session.commit()

    token = _generate_token(user)
    return jsonify({
        "token": token,
        "user": _user_to_dict(user),
    }), 200


@bp.route("/change-password", methods=["POST"])
@token_required
def change_password(current_user):
    """
    Change the authenticated user's password.
    """
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "Current and new passwords are required."}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters."}), 400

    is_valid, _ = verify_password(current_user.password_hash, current_password)
    if not is_valid:
        return jsonify({"error": "Current password is incorrect."}), 401

    current_user.password_hash = hash_password(new_password)
    db.session.commit()

    logger.info("Password changed: user_id=%d", current_user.id)
    _write_audit_log(
        current_user.id,
        "password_changed",
        None,
        council_id=current_user.council_id,
    )
    return jsonify({"message": "Password changed successfully."}), 200


@bp.route("/me", methods=["GET"])
@token_required
def get_me(current_user):
    """Return the authenticated user's own profile."""
    return jsonify({
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "phone": getattr(current_user, "phone", None),
            "position": getattr(current_user, "position", None),
            "department": getattr(current_user, "department", None),
            "council_id": current_user.council_id,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
            "last_login": current_user.last_login.isoformat() if getattr(current_user, "last_login", None) else None,
        }
    }), 200


@bp.route("/me", methods=["PATCH"])
@token_required
def update_me(current_user):
    """
    Update the authenticated user's own profile.
    Allowed fields: first_name, last_name, phone, position, department
    """
    data = request.get_json(silent=True) or {}

    allowed = {"first_name", "last_name", "phone", "position", "department"}
    updated = {}
    for field in allowed:
        if field in data:
            val = (data[field] or "").strip() if isinstance(data[field], str) else data[field]
            setattr(current_user, field, val or None)
            updated[field] = val

    if not updated:
        return jsonify({"error": "No valid fields provided."}), 400

    db.session.commit()
    logger.info("Profile updated: user_id=%d fields=%s", current_user.id, list(updated.keys()))
    return jsonify({
        "message": "Profile updated successfully.",
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "phone": getattr(current_user, "phone", None),
            "position": getattr(current_user, "position", None),
            "department": getattr(current_user, "department", None),
        }
    }), 200


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    """
    Request a password reset email.
    Accepts { "email": "..." } and sends a reset link if the account exists.
    Always returns 200 to avoid email enumeration.
    """
    import secrets

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "If an account exists for that email, a reset link has been sent."}), 200

    user = User.query.filter_by(email_hmac=hmac_index(email)).first()
    if user:
        token = secrets.token_urlsafe(48)
        user.reset_token = token
        user.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        db.session.commit()

        try:
            from app.common import email_service
            email_service.send_password_reset(email, user.first_name, token)
        except Exception as exc:
            logger.warning("Password reset email failed for user %d: %s", user.id, exc)

    return jsonify({"message": "If an account exists for that email, a reset link has been sent."}), 200


@bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Complete a password reset using the token from the email link.
    Accepts { "token": "...", "new_password": "..." }
    """
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("new_password") or ""

    if not token or not new_password:
        return jsonify({"error": "Token and new password are required."}), 400

    if len(new_password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    user = User.query.filter_by(reset_token=token).first()
    if not user:
        return jsonify({"error": "Invalid or expired reset token."}), 400

    expiry = user.reset_token_expiry
    if expiry and expiry.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        return jsonify({"error": "Reset token has expired. Please request a new one."}), 400

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()

    _write_audit_log(user.id, "password_reset", "Password reset via token")

    try:
        from app.common.notifications import notify
        notify(
            user_id=user.id,
            ntype="password_reset",
            title="Password changed",
            message="Your GrantThrive password was successfully reset.",
            link=None,
        )
    except Exception as exc:
        logger.warning("Password reset notification failed: %s", exc)

    return jsonify({"message": "Password reset successfully. You can now log in."}), 200