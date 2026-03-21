"""
GrantThrive — Council Registration Routes
==========================================
Handles self-service registration for:
  - council_admin  (first registrant from a government email domain)

Rules:
  1. Email must belong to a recognised government domain (.gov.au, .govt.nz, etc.)
  2. If no council_admin already exists for that email domain → assign council_admin role,
     place account in the approval queue (is_active=False, is_approved=False).
  3. If a council_admin already exists for that domain → reject with HTTP 409 and
     instruct the applicant to contact their Council Administrator.

Endpoint:
  POST  /register/council
        Alias: POST /register  (when user_type is council | council_admin | council_staff)
"""
import logging
from flask import request, jsonify, g

from app import db, limiter
from app.models import User
from app.auth import bp
from app.auth.helpers import (
    _find_user_by_email,
    _user_to_dict,
    _write_audit_log,
)

logger = logging.getLogger(__name__)

# Accepted aliases that all map to the council_admin self-registration path
COUNCIL_ALIASES = {"council", "council_admin", "council_staff"}

# Government email domain suffixes accepted for council registration
_GOVT_SUFFIXES = (
    ".gov.au",
    ".govt.nz",
    ".gov.nz",
    ".gov.uk",
    ".gov",
    ".edu.au",
    ".edu.nz",
)


def _is_govt_email(email: str) -> bool:
    domain = email.split("@")[-1].lower()
    return any(domain.endswith(suffix) for suffix in _GOVT_SUFFIXES)


def _register_council_user(data: dict):
    """
    Core registration logic for council_admin self-registration.
    Returns a Flask response tuple (response, status_code).
    """
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    phone = (data.get("phone") or "").strip() or None
    organisation = (data.get("organisation") or data.get("organization_name") or "").strip() or None
    abn = (data.get("abn") or "").strip() or None
    email_opt_in = bool(data.get("email_opt_in", True))
    position = (data.get("position") or "").strip() or None
    department = (data.get("department") or "").strip() or None
    requested_subdomain = (data.get("subdomain") or "").strip() or None

    if not all([email, password, first_name, last_name]):
        return jsonify({"error": "Email, password, first name, and last name are required."}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    # ── Government domain check ───────────────────────────────────────────────
    if not _is_govt_email(email):
        return jsonify({
            "error": (
                "Council accounts require a government email address "
                "(e.g. name@council.gov.au). Please use your official council email."
            )
        }), 400

    # ── Domain-uniqueness check ───────────────────────────────────────────────
    # Email is stored encrypted; we must decrypt in Python to compare domains.
    # This is a low-frequency operation (registration only) so a full-table scan
    # over council_admin rows is acceptable.
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

    # ── Duplicate email check ─────────────────────────────────────────────────
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
        role="council_admin",
        council_id=council_id,
        is_active=False,      # pending system_admin approval
        is_approved=False,
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
        logger.exception("Council registration failed: %s", exc)
        return jsonify({"error": "Could not complete registration."}), 500

    _write_audit_log(
        user.id,
        "register",
        f"email={email} role=council_admin (pending approval)",
        council_id=council_id,
    )

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
    except Exception as exc:
        logger.warning("Registration notification failed: %s", exc)

    return jsonify({
        "message": "Registration successful. Your account is pending approval.",
        "user": _user_to_dict(user),
        "requires_approval": True,
    }), 201


@bp.route("/register/council", methods=["POST"])
@limiter.limit("5 per minute")
def register_council():
    """
    Dedicated endpoint for council_admin self-registration.
    Accepts user_type: 'council' | 'council_admin' | 'council_staff'.
    All aliases are treated as a council_admin self-registration request.
    """
    data = request.get_json(silent=True) or {}
    return _register_council_user(data)
