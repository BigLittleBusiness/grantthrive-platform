"""
GrantThrive — Shared Auth Routes
==================================
Endpoints used by ALL roles:
  POST   /login
  POST   /logout
  POST   /verify-token
  POST   /demo-login          (non-production only)
  POST   /change-password     (authenticated)
  GET    /me                  (authenticated)
  PATCH  /me                  (authenticated)
  POST   /forgot-password
  POST   /reset-password
"""
import logging
from datetime import timedelta

from flask import request, jsonify, current_app, g

from app import db, limiter
from app.models import User, Council
from app.auth import bp
from app.auth.helpers import (
    _utcnow,
    _normalize_dt,
    _find_user_by_email,
    _generate_token,
    _decode_token,
    _user_to_dict,
    _write_audit_log,
    token_required,
    hash_password,
    verify_password,
    JWT_ALGORITHM,
    JWT_ADMIN_REFRESH_MINS,
)

logger = logging.getLogger(__name__)


# ── Login ─────────────────────────────────────────────────────────────────────

@bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400
    try:
        user = _find_user_by_email(email)
    except Exception as exc:
        db.session.rollback()
        logger.exception("Login DB error: %s", exc)
        return jsonify({"error": "Login failed. Please try again."}), 500
    if not user:
        return jsonify({"error": "Invalid email or password."}), 401
    is_valid, needs_rehash = verify_password(user.password_hash, password)
    if not is_valid:
        return jsonify({"error": "Invalid email or password."}), 401
    if not user.is_active:
        return jsonify({"error": "Your account is pending approval."}), 403
    if needs_rehash:
        try:
            user.password_hash = hash_password(password)
            db.session.commit()
        except Exception:
            db.session.rollback()
    try:
        user.last_login = _utcnow()
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning("Could not update last_login for user %d: %s", user.id, exc)
    _write_audit_log(user.id, "login", None, council_id=user.council_id)
    token = _generate_token(user)
    return jsonify({"token": token, "user": _user_to_dict(user)}), 200


# ── Logout ────────────────────────────────────────────────────────────────────

@bp.route("/logout", methods=["POST"])
@token_required
def logout(current_user):
    _write_audit_log(current_user.id, "logout", None, council_id=current_user.council_id)
    return jsonify({"message": "Logged out successfully."}), 200


# ── Verify token ──────────────────────────────────────────────────────────────

@bp.route("/verify-token", methods=["POST"])
def verify_token():
    import jwt as pyjwt
    data = request.get_json(silent=True) or {}
    token = data.get("token") or ""
    auth_header = request.headers.get("Authorization", "")
    if not token and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
    if not token:
        return jsonify({"valid": False, "error": "No token provided."}), 401
    try:
        payload = _decode_token(token)
    except pyjwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token has expired."}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token."}), 401
    user = db.session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return jsonify({"valid": False, "error": "User not found or inactive."}), 401
    response_body = {"valid": True, "user": _user_to_dict(user)}
    if user.role == "system_admin":
        exp_ts = payload.get("exp", 0)
        now_ts = _utcnow().timestamp()
        remaining_mins = (exp_ts - now_ts) / 60
        if remaining_mins < JWT_ADMIN_REFRESH_MINS:
            response_body["new_token"] = _generate_token(user)
    return jsonify(response_body), 200


# ── Demo login (non-production only) ─────────────────────────────────────────

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
    return jsonify({"token": token, "user": _user_to_dict(user)}), 200


# ── Profile (all authenticated roles) ────────────────────────────────────────

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


# ── Change password (authenticated) ──────────────────────────────────────────

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


# ── Forgot / reset password (unauthenticated) ─────────────────────────────────

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
