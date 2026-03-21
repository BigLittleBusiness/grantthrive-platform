"""
GrantThrive — Community & Consultant Registration Routes
=========================================================
Handles self-service registration for:
  - community_member
  - professional_consultant

These roles are activated immediately on registration (no approval queue).

Endpoint:
  POST  /register/community
        Alias: POST /register  (when user_type is community_member or professional_consultant)
"""
import logging
from flask import request, jsonify, g

from app import db, limiter
from app.models import User
from app.auth import bp
from app.auth.helpers import (
    _utcnow,
    _find_user_by_email,
    _generate_token,
    _user_to_dict,
    _write_audit_log,
)

logger = logging.getLogger(__name__)

# Roles handled by this module
OPEN_ROLES = {"community_member", "professional_consultant"}


def _register_open_user(data: dict):
    """
    Core registration logic for community_member and professional_consultant.
    Returns a Flask response tuple (response, status_code).
    """
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

    role = raw_user_type if raw_user_type in OPEN_ROLES else "community_member"

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

    user = User(
        username=username,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=role,
        council_id=council_id,
        is_active=True,
        is_approved=True,
        organisation=organisation,
        abn=abn,
        email_opt_in=email_opt_in,
    )
    user.set_email(email)
    user.set_password(password)

    try:
        db.session.add(user)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception("Community registration failed: %s", exc)
        return jsonify({"error": "Could not complete registration."}), 500

    _write_audit_log(user.id, "register", f"email={email} role={role}", council_id=council_id)

    try:
        from app.common.notifications import notify
        from app.common import email_service
        notify(
            user_id=user.id,
            ntype="registration_confirmed",
            title="Welcome to GrantThrive",
            message="Your account has been created successfully.",
            link="portal/community/dashboard",
            send_email_fn=lambda: email_service.send_registration_confirmation(email, first_name),
        )
    except Exception as exc:
        logger.warning("Registration notification failed: %s", exc)

    return jsonify({
        "message": "Registration successful.",
        "user": _user_to_dict(user),
        "requires_approval": False,
    }), 201


@bp.route("/register/community", methods=["POST"])
@limiter.limit("5 per minute")
def register_community():
    """
    Dedicated endpoint for community_member and professional_consultant self-registration.
    Accepts user_type: 'community_member' | 'professional_consultant'.
    Defaults to community_member for any unrecognised user_type.
    """
    data = request.get_json(silent=True) or {}
    return _register_open_user(data)
