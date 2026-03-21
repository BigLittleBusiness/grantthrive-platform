"""
GrantThrive — Authentication Routes
=====================================
Provides JWT-based authentication endpoints consumed by all GrantThrive UI apps
via the shared @grantthrive/auth library.
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify, current_app, g
from sqlalchemy.exc import SQLAlchemyError

from app.common.password import hash_password, verify_password
from app.common.encryption import hmac_index
from app import db, limiter
from app.auth import bp
from app.models import User, Council

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7
JWT_ADMIN_EXPIRY_HRS = 2
JWT_ADMIN_REFRESH_MINS = 15


# ── Helpers ───────────────────────────────────────────────────────────────────

def _utcnow():
    return datetime.now(timezone.utc)


def _normalize_dt(dt):
    """Return timezone-aware UTC datetime."""
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _find_user_by_email(email: str):
    """Find user by email_hmac with DB safety."""
    if not email:
        return None
    try:
        return User.query.filter_by(email_hmac=hmac_index(email.strip().lower())).first()
    except SQLAlchemyError as exc:
        db.session.rollback()
        logger.exception("Failed querying user by email_hmac: %s", exc)
        raise


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


def token_required(f):
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

        try:
            user = db.session.get(User, int(payload["sub"]))
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed loading user from token: %s", exc)
            return jsonify({"error": "Failed to validate user."}), 500

        if not user or not user.is_active:
            return jsonify({"error": "User account not found or inactive."}), 401

        return f(user, *args, **kwargs)

    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator


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


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/login", methods=["POST"])
@limiter.limit(
    "10 per 15 minutes",
    error_message="Too many login attempts from this IP. Please try again in 15 minutes.",
)
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    try:
        user = _find_user_by_email(email)
    except Exception:
        return jsonify({"error": "Database error during login."}), 500

    if not user:
        logger.warning("Failed login attempt for email: %s", email)
        return jsonify({"error": "Invalid email or password."}), 401

    is_valid, needs_rehash = verify_password(user.password_hash, password)
    if not is_valid:
        logger.warning("Failed login attempt for user_id=%d", user.id)
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.is_active or not user.is_approved:
        return jsonify({
            "error": "Your account is pending approval or has been suspended."
        }), 403

    current_council = getattr(g, "council", None)
    if current_council and user.role != "system_admin":
        if user.council_id != current_council.id:
            logger.warning(
                "Cross-tenant login attempt: user_id=%d (council_id=%s) tried via %s (council_id=%d)",
                user.id, user.council_id, current_council.subdomain, current_council.id,
            )
            return jsonify({"error": "Invalid email or password."}), 401

    try:
        if needs_rehash:
            user.password_hash = hash_password(password)
            logger.info("Rehashed password for user_id=%d", user.id)

        user.last_login = _utcnow()
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Login commit failed: %s", exc)
        return jsonify({"error": "Could not complete login."}), 500

    token = _generate_token(user)
    _write_audit_log(user.id, "login", f"role={user.role}", council_id=user.council_id)

    return jsonify({
        "token": token,
        "user": _user_to_dict(user),
    }), 200


@bp.route("/logout", methods=["POST"])
def logout():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
            user_id = int(payload.get("sub", 0))
            council_id = payload.get("council_id")
            _write_audit_log(user_id, "logout", None, council_id=council_id)
        except jwt.InvalidTokenError:
            pass

    return jsonify({"message": "Logged out successfully."}), 200


@bp.route("/register", methods=["POST"])
def register():
    import re as _re

    GOVT_DOMAIN_PATTERNS = [
        r"\.gov\.au$",
        r"\.govt\.nz$",
        r"\.gov\.nz$",
        r"\.gov\.uk$",
        r"\.gov$",
        r"\.edu\.au$",
        r"\.edu\.nz$",
    ]

    def _is_govt_email(addr: str) -> bool:
        domain = addr.split("@")[-1].lower()
        return any(_re.search(p, domain) for p in GOVT_DOMAIN_PATTERNS)

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    raw_user_type = (data.get("user_type") or data.get("role") or "community_member").strip().lower()
    organisation = (data.get("organisation") or data.get("organization_name") or "").strip() or None
    abn = (data.get("abn") or "").strip() or None
    email_opt_in = bool(data.get("email_opt_in", True))

    if not all([email, password, first_name, last_name]):
        return jsonify({"error": "Email, password, first name, and last name are required."}), 400

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    OPEN_ROLES = {"community_member", "professional_consultant"}
    COUNCIL_ALIASES = {"council", "council_admin", "council_staff"}

    is_council_registration = raw_user_type in COUNCIL_ALIASES
    status_active = False
    approved = False

    if is_council_registration:
        if not _is_govt_email(email):
            return jsonify({
                "error": (
                    "Council accounts require a government email address "
                    "(e.g. name@council.gov.au). Please use your official council email."
                )
            }), 400

        email_domain = email.split("@")[-1].lower()

        try:
            council_admins = User.query.filter_by(role="council_admin").all()
        except Exception as exc:
            db.session.rollback()
            logger.exception("Failed checking existing council admins: %s", exc)
            return jsonify({"error": "Could not validate council registration."}), 500

        existing_admin = next(
            (
                u for u in council_admins
                if getattr(u, "email", None)
                and u.email.split("@")[-1].lower() == email_domain
            ),
            None,
        )

        if existing_admin:
            return jsonify({
                "error": (
                    "A Council Administrator account already exists for your organisation. "
                    "Please contact your Council Administrator to be added as a staff member."
                )
            }), 409

        role = "council_admin"
        status_active = False
        approved = False

    elif raw_user_type in OPEN_ROLES:
        role = raw_user_type
        status_active = True
        approved = True

    else:
        role = "community_member"
        status_active = True
        approved = True

    try:
        existing_user = _find_user_by_email(email)
    except Exception:
        return jsonify({"error": "Database error during registration."}), 500

    if existing_user:
        return jsonify({"error": "An account with this email already exists."}), 409

    current_council = getattr(g, "council", None)
    council_id = current_council.id if current_council else None

    base_username = email.split("@")[0]
    username = base_username
    counter = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    position = (data.get("position") or "").strip() or None
    department = (data.get("department") or "").strip() or None
    requested_subdomain = (data.get("subdomain") or "").strip() or None

    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        council_id=council_id,
        is_active=status_active,
        is_approved=approved,
        organisation=organisation,
        abn=abn,
        email_opt_in=email_opt_in,
        position=position,
        department=department,
        requested_subdomain=requested_subdomain,
    )
    user.set_email(email)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Registration failed: %s", exc)
        return jsonify({"error": "Could not complete registration."}), 500

    _write_audit_log(user.id, "register", f"email={email} role={role}", council_id=council_id)

    try:
        from app.common.notifications import notify
        from app.common import email_service

        notify(
            user_id=user.id,
            ntype="registration_confirmed",
            title="Welcome to GrantThrive",
            message=(
                "Your account has been created and is pending approval."
                if not approved else
                "Your account has been created successfully."
            ),
            link="portal/community/dashboard",
            send_email_fn=lambda: email_service.send_registration_confirmation(email, first_name),
        )
    except Exception as exc:
        logger.warning("Registration notification failed: %s", exc)

    return jsonify({
        "message": (
            "Registration successful. Your account is pending approval."
            if not approved else
            "Registration successful."
        ),
        "user": _user_to_dict(user),
        "requires_approval": not approved,
    }), 201


@bp.route("/verify-token", methods=["POST"])
def verify_token():
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
        now_ts = _utcnow().timestamp()
        remaining_mins = (exp_ts - now_ts) / 60
        if remaining_mins < JWT_ADMIN_REFRESH_MINS:
            response_body["new_token"] = _generate_token(user)

    return jsonify(response_body), 200


@bp.route("/demo-login", methods=["POST"])
def demo_login():
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
    user = _find_user_by_email(profile["email"])

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

    try:
        user.last_login = _utcnow()
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Demo login failed: %s", exc)
        return jsonify({"error": "Demo login failed."}), 500

    token = _generate_token(user)
    return jsonify({
        "token": token,
        "user": _user_to_dict(user),
    }), 200


@bp.route("/change-password", methods=["POST"])
@token_required
def change_password(current_user):
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

    try:
        current_user.password_hash = hash_password(new_password)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Change password failed: %s", exc)
        return jsonify({"error": "Could not change password."}), 500

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
    return jsonify({"user": _user_to_dict(current_user)}), 200


@bp.route("/me", methods=["PATCH"])
@token_required
def update_me(current_user):
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

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Profile update failed: %s", exc)
        return jsonify({"error": "Could not update profile."}), 500

    return jsonify({
        "message": "Profile updated successfully.",
        "user": _user_to_dict(current_user),
    }), 200


@bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    import secrets

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"message": "If an account exists for that email, a reset link has been sent."}), 200

    try:
        user = _find_user_by_email(email)
    except Exception:
        return jsonify({"message": "If an account exists for that email, a reset link has been sent."}), 200

    if user:
        try:
            token = secrets.token_urlsafe(48)
            user.reset_token = token
            user.reset_token_expiry = _utcnow() + timedelta(hours=1)
            db.session.commit()

            try:
                from app.common import email_service
                email_service.send_password_reset(email, user.first_name, token)
            except Exception as exc:
                logger.warning("Password reset email failed for user %d: %s", user.id, exc)

        except Exception as exc:
            db.session.rollback()
            logger.exception("Forgot password failed: %s", exc)

    return jsonify({"message": "If an account exists for that email, a reset link has been sent."}), 200


@bp.route("/reset-password", methods=["POST"])
def reset_password():
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

    expiry = _normalize_dt(user.reset_token_expiry)
    if expiry and expiry < _utcnow():
        return jsonify({"error": "Reset token has expired. Please request a new one."}), 400

    try:
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Reset password failed: %s", exc)
        return jsonify({"error": "Could not reset password."}), 500

    _write_audit_log(user.id, "password_reset", "Password reset via token", council_id=user.council_id)

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