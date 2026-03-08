"""
GrantThrive — Stepwise Registration API
=========================================
Multi-step registration flows for all user roles.

Each role has its own registration journey with distinct steps.
Progress is tracked server-side using a short-lived registration session token
(a signed JWT with a short expiry) that carries the partial profile between steps.

Registration flows by role:
  ─────────────────────────────────────────────────────────────────────────────
  community_member / professional_consultant  (self-service, 3 steps)
    Step 1 — Account basics:    email, password, first_name, last_name
    Step 2 — Profile details:   phone, address, postcode, organisation (optional)
    Step 3 — Confirm & submit:  review, accept terms, create account

  council_staff  (invited by council_admin, 3 steps)
    Step 1 — Validate invite:   invite_token (pre-issued by council_admin)
    Step 2 — Set credentials:   password, first_name, last_name, phone
    Step 3 — Confirm & submit:  review, create account

  council_admin  (provisioned by system_admin, 2 steps)
    Step 1 — Council selection: council_id (must exist), validated by system_admin token
    Step 2 — Set credentials:   email, password, first_name, last_name, phone

  system_admin  (created via the Super Admin management screen — see system_admin/routes.py)
    No self-registration flow. Created only by existing system_admin users.
  ─────────────────────────────────────────────────────────────────────────────

Endpoints:
  POST /auth/register/start                 — Begin registration, returns session token
  POST /auth/register/step/<int:step>       — Submit data for a step, returns updated token
  POST /auth/register/complete              — Finalise and create the account
  GET  /auth/register/status                — Check registration session status
  POST /auth/register/invite/validate       — Validate a council_staff invite token

Session token payload:
  {
    "reg_session": true,
    "role":        "community_member",
    "step":        2,          // highest completed step
    "data":        { ... },    // accumulated form data (no passwords stored)
    "exp":         <timestamp> // 1 hour from last activity
  }

Note: passwords are NEVER stored in the session token.
      They are only accepted at the final /complete step.
"""

import jwt
import logging
import secrets
from datetime import datetime, timedelta, timezone

from flask import request, jsonify, current_app

from app import db, limiter
from app.auth import bp
from app.models import User, Council

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

JWT_ALGORITHM        = "HS256"
REG_SESSION_EXPIRY   = timedelta(hours=1)
INVITE_TOKEN_EXPIRY  = timedelta(hours=48)

# Roles that can self-register
SELF_REGISTER_ROLES = {"community_member", "professional_consultant"}

# Steps required per role
ROLE_STEPS = {
    "community_member":        3,
    "professional_consultant": 3,
    "council_staff":           3,
    "council_admin":           2,
}

# Fields collected at each step per role
STEP_FIELDS = {
    "community_member": {
        1: ["email", "first_name", "last_name"],          # password excluded from token
        2: ["phone", "address", "postcode", "organisation"],
        3: ["accept_terms"],
    },
    "professional_consultant": {
        1: ["email", "first_name", "last_name"],
        2: ["phone", "address", "postcode", "organisation", "abn"],
        3: ["accept_terms"],
    },
    "council_staff": {
        1: ["invite_token"],
        2: ["first_name", "last_name", "phone"],          # password excluded from token
        3: ["accept_terms"],
    },
    "council_admin": {
        1: ["council_id"],
        2: ["email", "first_name", "last_name", "phone"], # password excluded from token
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _issue_reg_token(role: str, step: int, data: dict) -> str:
    """Issue a short-lived registration session JWT."""
    payload = {
        "reg_session": True,
        "role":        role,
        "step":        step,
        "data":        data,
        "iat":         datetime.now(timezone.utc),
        "exp":         datetime.now(timezone.utc) + REG_SESSION_EXPIRY,
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=JWT_ALGORITHM)


def _decode_reg_token(token: str) -> tuple[dict | None, str | None]:
    """Decode a registration session JWT. Returns (payload, error)."""
    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[JWT_ALGORITHM],
        )
        if not payload.get("reg_session"):
            return None, "Invalid registration session token."
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Registration session has expired. Please start again."
    except jwt.InvalidTokenError:
        return None, "Invalid registration session token."


def _get_reg_token_from_request() -> str | None:
    """Extract registration session token from Authorization header or body."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    data = request.get_json(silent=True) or {}
    return data.get("registration_token")


def _validate_email(email: str) -> str | None:
    """Return error string if email is invalid, else None."""
    import re
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return "Invalid email address."
    if User.query.filter_by(email=email).first():
        return "An account with this email already exists."
    return None


def _validate_password(password: str) -> str | None:
    """Return error string if password is too weak, else None."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def _generate_username(email: str) -> str:
    """Generate a unique username from an email address."""
    base = email.split("@")[0]
    username = base
    counter  = 1
    while User.query.filter_by(username=username).first():
        username = f"{base}{counter}"
        counter += 1
    return username


# ── Step 1: Start registration ────────────────────────────────────────────────

@bp.route("/register/start", methods=["POST"])
@limiter.limit("20 per hour")
def register_start():
    """
    Begin a registration session.

    Request body:
        { "role": "community_member" | "professional_consultant" | "council_staff" | "council_admin" }

    For council_admin, requires a valid system_admin JWT in the Authorization header.

    Response (200):
        {
          "registration_token": "<jwt>",
          "role": "...",
          "total_steps": 3,
          "current_step": 1,
          "step_fields": ["email", "first_name", "last_name"]
        }
    """
    data = request.get_json(silent=True) or {}
    role = data.get("role", "").strip().lower()

    if role not in ROLE_STEPS:
        return jsonify({
            "error": f"Invalid role. Must be one of: {', '.join(ROLE_STEPS.keys())}"
        }), 400

    # council_admin provisioning requires a system_admin token
    if role == "council_admin":
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "system_admin authentication required to provision council_admin accounts."}), 401
        try:
            payload = jwt.decode(
                auth_header.split(" ", 1)[1],
                current_app.config["SECRET_KEY"],
                algorithms=[JWT_ALGORITHM],
            )
            if payload.get("role") != "system_admin":
                return jsonify({"error": "Only system_admin users can provision council_admin accounts."}), 403
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid authentication token."}), 401

    token = _issue_reg_token(role=role, step=0, data={})

    return jsonify({
        "registration_token": token,
        "role":               role,
        "total_steps":        ROLE_STEPS[role],
        "current_step":       1,
        "step_fields":        STEP_FIELDS[role].get(1, []),
        "message":            f"Registration started for role '{role}'. Proceed to step 1.",
    }), 200


# ── Step N: Submit step data ──────────────────────────────────────────────────

@bp.route("/register/step/<int:step>", methods=["POST"])
@limiter.limit("30 per hour")
def register_step(step: int):
    """
    Submit data for a registration step.

    Requires the registration_token from /register/start (or previous step).
    Returns an updated registration_token with accumulated data.

    Request body:
        {
          "registration_token": "<jwt>",
          ... step-specific fields ...
        }
    """
    token = _get_reg_token_from_request()
    if not token:
        return jsonify({"error": "Registration token is required."}), 400

    payload, error = _decode_reg_token(token)
    if error:
        return jsonify({"error": error}), 400

    role         = payload["role"]
    current_step = payload["step"]
    accumulated  = payload.get("data", {})
    total_steps  = ROLE_STEPS[role]

    # Steps must be submitted in order
    if step != current_step + 1:
        return jsonify({
            "error": f"Expected step {current_step + 1}, received step {step}.",
            "current_step": current_step,
        }), 400

    if step > total_steps:
        return jsonify({"error": "All steps already completed. Use /register/complete."}), 400

    data = request.get_json(silent=True) or {}

    # ── Role-specific step validation ─────────────────────────────────────────

    if role in ("community_member", "professional_consultant"):
        if step == 1:
            email      = (data.get("email") or "").strip().lower()
            first_name = (data.get("first_name") or "").strip()
            last_name  = (data.get("last_name") or "").strip()

            if not all([email, first_name, last_name]):
                return jsonify({"error": "email, first_name, and last_name are required."}), 400

            email_error = _validate_email(email)
            if email_error:
                return jsonify({"error": email_error}), 409

            accumulated.update({
                "email":      email,
                "first_name": first_name,
                "last_name":  last_name,
            })

        elif step == 2:
            # All fields optional at step 2
            for field in ["phone", "address", "postcode", "organisation", "abn"]:
                if field in data and data[field]:
                    accumulated[field] = str(data[field]).strip()

        elif step == 3:
            if not data.get("accept_terms"):
                return jsonify({"error": "You must accept the terms and conditions."}), 400
            accumulated["accept_terms"] = True

    elif role == "council_staff":
        if step == 1:
            invite_token = (data.get("invite_token") or "").strip()
            if not invite_token:
                return jsonify({"error": "invite_token is required."}), 400

            # Validate the invite token
            invite_payload, invite_error = _validate_invite_token_payload(invite_token)
            if invite_error:
                return jsonify({"error": invite_error}), 400

            accumulated.update({
                "invite_token":  invite_token,
                "council_id":    invite_payload["council_id"],
                "invited_email": invite_payload["email"],
            })

        elif step == 2:
            first_name = (data.get("first_name") or "").strip()
            last_name  = (data.get("last_name") or "").strip()
            if not all([first_name, last_name]):
                return jsonify({"error": "first_name and last_name are required."}), 400
            accumulated.update({
                "first_name": first_name,
                "last_name":  last_name,
                "phone":      (data.get("phone") or "").strip() or None,
            })

        elif step == 3:
            if not data.get("accept_terms"):
                return jsonify({"error": "You must accept the terms and conditions."}), 400
            accumulated["accept_terms"] = True

    elif role == "council_admin":
        if step == 1:
            council_id = data.get("council_id")
            if not council_id:
                return jsonify({"error": "council_id is required."}), 400
            council = db.session.get(Council, int(council_id))
            if not council or not council.is_active:
                return jsonify({"error": "Council not found or inactive."}), 404
            # Ensure no active council_admin already exists for this council
            existing_admin = User.query.filter_by(
                council_id=council.id, role="council_admin", is_active=True
            ).first()
            if existing_admin:
                return jsonify({"error": "This council already has an active admin account."}), 409
            accumulated.update({
                "council_id":   council.id,
                "council_name": council.name,
            })

        elif step == 2:
            email      = (data.get("email") or "").strip().lower()
            first_name = (data.get("first_name") or "").strip()
            last_name  = (data.get("last_name") or "").strip()
            if not all([email, first_name, last_name]):
                return jsonify({"error": "email, first_name, and last_name are required."}), 400
            email_error = _validate_email(email)
            if email_error:
                return jsonify({"error": email_error}), 409
            accumulated.update({
                "email":      email,
                "first_name": first_name,
                "last_name":  last_name,
                "phone":      (data.get("phone") or "").strip() or None,
            })

    # Issue updated token with incremented step
    new_token = _issue_reg_token(role=role, step=step, data=accumulated)
    is_final  = (step == total_steps)

    return jsonify({
        "registration_token": new_token,
        "role":               role,
        "total_steps":        total_steps,
        "current_step":       step,
        "is_final_step":      is_final,
        "next_step_fields":   STEP_FIELDS[role].get(step + 1, []) if not is_final else [],
        "message":            f"Step {step} completed." + (" Ready to complete registration." if is_final else ""),
    }), 200


# ── Complete registration ─────────────────────────────────────────────────────

@bp.route("/register/complete", methods=["POST"])
@limiter.limit("10 per hour")
def register_complete():
    """
    Finalise registration and create the user account.

    Requires the registration_token from the final step AND the user's chosen password.
    Passwords are only accepted at this final step and are never stored in the session token.

    Request body:
        {
          "registration_token": "<jwt>",
          "password":           "..."
        }

    Response (201):
        {
          "message": "Account created successfully.",
          "user": { ... },
          "requires_approval": true | false
        }
    """
    token = _get_reg_token_from_request()
    if not token:
        return jsonify({"error": "Registration token is required."}), 400

    payload, error = _decode_reg_token(token)
    if error:
        return jsonify({"error": error}), 400

    role        = payload["role"]
    step        = payload["step"]
    accumulated = payload.get("data", {})
    total_steps = ROLE_STEPS[role]

    if step < total_steps:
        return jsonify({
            "error": f"Registration is not complete. You are on step {step} of {total_steps}.",
            "current_step": step,
            "total_steps":  total_steps,
        }), 400

    data     = request.get_json(silent=True) or {}
    password = data.get("password") or ""

    # council_staff uses the invited email; others provide their own
    if role == "council_staff":
        email = accumulated.get("invited_email")
        if not email:
            return jsonify({"error": "Invite token data is missing. Please start registration again."}), 400
    else:
        email = accumulated.get("email")

    if not email:
        return jsonify({"error": "Email is missing from registration session. Please start again."}), 400

    # Re-validate email uniqueness at completion time
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    password_error = _validate_password(password)
    if password_error:
        return jsonify({"error": password_error}), 400

    # Determine council and activation state
    council_id       = accumulated.get("council_id")
    requires_approval = True

    if role == "council_admin":
        # council_admin accounts are created active (provisioned by system_admin)
        is_active = True
        requires_approval = False
    elif role == "council_staff":
        # council_staff accounts are created active (invited by council_admin)
        is_active = True
        requires_approval = False
    else:
        # community_member and professional_consultant require admin approval
        is_active = False
        requires_approval = True

    username = _generate_username(email)

    user = User(
        username     = username,
        email        = email,
        first_name   = accumulated.get('first_name', ''),
        last_name    = accumulated.get('last_name', ''),
        phone        = accumulated.get('phone'),
        role         = role,
        council_id   = council_id,
        is_active    = is_active,
        is_approved  = not requires_approval,
        organisation = accumulated.get('organisation'),
        abn          = accumulated.get('abn'),
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    logger.info(
        "Registration complete: user_id=%d email=%s role=%s council_id=%s active=%s",
        user.id, email, role, council_id, is_active,
    )

    from app.auth.routes import _user_to_dict, _write_audit_log
    _write_audit_log(user.id, "register_complete", f"role={role}", council_id=council_id)

    return jsonify({
        "message":           "Account created successfully." + (
            " Your account is pending approval." if requires_approval else ""
        ),
        "user":              _user_to_dict(user),
        "requires_approval": requires_approval,
    }), 201


# ── Registration status ───────────────────────────────────────────────────────

@bp.route("/register/status", methods=["GET"])
def register_status():
    """
    Check the current state of a registration session.

    Requires the registration_token in the Authorization header.

    Response (200):
        {
          "role": "...",
          "current_step": 2,
          "total_steps": 3,
          "completed_fields": ["email", "first_name", ...],
          "next_step_fields": ["phone", "address", ...]
        }
    """
    token = _get_reg_token_from_request()
    if not token:
        return jsonify({"error": "Registration token is required."}), 400

    payload, error = _decode_reg_token(token)
    if error:
        return jsonify({"error": error}), 400

    role        = payload["role"]
    step        = payload["step"]
    accumulated = payload.get("data", {})
    total_steps = ROLE_STEPS[role]

    # Return completed fields (excluding any sensitive data)
    safe_fields = {k: v for k, v in accumulated.items()
                   if k not in ("invite_token",)}

    return jsonify({
        "role":              role,
        "current_step":      step,
        "total_steps":       total_steps,
        "is_complete":       step >= total_steps,
        "completed_fields":  safe_fields,
        "next_step_fields":  STEP_FIELDS[role].get(step + 1, []),
    }), 200


# ── Invite token management ───────────────────────────────────────────────────

def _validate_invite_token_payload(invite_token: str) -> tuple[dict | None, str | None]:
    """Validate a council_staff invite token. Returns (payload, error)."""
    try:
        payload = jwt.decode(
            invite_token,
            current_app.config["SECRET_KEY"],
            algorithms=[JWT_ALGORITHM],
        )
        if not payload.get("invite"):
            return None, "Invalid invite token."
        if payload.get("role") != "council_staff":
            return None, "This invite is not for a council_staff account."
        # Check the invited email is not already registered
        if User.query.filter_by(email=payload.get("email")).first():
            return None, "An account with this email already exists."
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, "Invite token has expired. Please request a new invitation."
    except jwt.InvalidTokenError:
        return None, "Invalid invite token."


@bp.route("/register/invite/validate", methods=["POST"])
def validate_invite():
    """
    Validate a council_staff invite token before beginning registration.

    Request body:
        { "invite_token": "..." }

    Response (200):
        { "valid": true, "email": "...", "council_name": "...", "role": "council_staff" }
    """
    data         = request.get_json(silent=True) or {}
    invite_token = (data.get("invite_token") or "").strip()

    if not invite_token:
        return jsonify({"error": "invite_token is required."}), 400

    invite_payload, error = _validate_invite_token_payload(invite_token)
    if error:
        return jsonify({"valid": False, "error": error}), 400

    council = db.session.get(Council, invite_payload.get("council_id"))
    council_name = council.name if council else "Unknown Council"

    return jsonify({
        "valid":        True,
        "email":        invite_payload.get("email"),
        "council_name": council_name,
        "role":         "council_staff",
    }), 200


@bp.route("/register/invite/create", methods=["POST"])
def create_invite():
    """
    Issue a council_staff invite token (council_admin or system_admin only).

    Request body:
        { "email": "...", "council_id": 1 }

    Response (201):
        { "invite_token": "...", "expires_at": "..." }
    """
    from app.common.permissions import _resolve_user_from_token
    user, error = _resolve_user_from_token()
    if error:
        return jsonify({"error": error}), 401

    if user.role not in ("council_admin", "system_admin"):
        return jsonify({"error": "Only council_admin or system_admin can issue invitations."}), 403

    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return jsonify({"error": "email is required."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    # Determine council
    if user.role == "system_admin":
        council_id = data.get("council_id")
        if not council_id:
            return jsonify({"error": "council_id is required."}), 400
    else:
        council_id = user.council_id

    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({"error": "Council not found."}), 404

    expires_at = datetime.now(timezone.utc) + INVITE_TOKEN_EXPIRY

    invite_payload = {
        "invite":     True,
        "role":       "council_staff",
        "email":      email,
        "council_id": council_id,
        "invited_by": user.id,
        "iat":        datetime.now(timezone.utc),
        "exp":        expires_at,
    }
    invite_token = jwt.encode(
        invite_payload,
        current_app.config["SECRET_KEY"],
        algorithm=JWT_ALGORITHM,
    )

    logger.info(
        "Invite created: email=%s council_id=%d by user_id=%d",
        email, council_id, user.id,
    )

    return jsonify({
        "invite_token": invite_token,
        "email":        email,
        "council_name": council.name,
        "expires_at":   expires_at.isoformat(),
        "message":      f"Invite token created for {email}. Valid for 48 hours.",
    }), 201
