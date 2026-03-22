"""
System Admin Management API
============================
Endpoints for GrantThrive staff (system_admin) to manage other system_admin
accounts.  All routes require an authenticated system_admin JWT.

Routes
------
GET    /api/system-admins              — List all system_admin users (paginated)
POST   /api/system-admins              — Create a new system_admin user
GET    /api/system-admins/<id>         — Get a single system_admin user
PATCH  /api/system-admins/<id>         — Update a system_admin user
DELETE /api/system-admins/<id>         — Deactivate (soft-delete) a system_admin user
POST   /api/system-admins/<id>/restore — Reactivate a deactivated system_admin user

Security
--------
- All endpoints require a valid JWT with role == 'system_admin'.
- A system_admin cannot deactivate or delete their own account.
- At least one active system_admin must remain at all times.
- Password changes require the new password to meet minimum strength requirements.
- All mutations are written to the audit_log table.
"""
import logging
import re
from datetime import datetime, timezone

from flask import request, jsonify, current_app
from app.common.password import hash_password  # noqa: F401 — used via user.set_password()

from app import db, limiter
from app.models import User, AuditLog
from app.auth.routes import role_required, _write_audit_log
from app.system_admin import bp

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_PASSWORD_LENGTH = 12
PASSWORD_PATTERN    = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]).{12,}$'
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def _admin_to_dict(user: User) -> dict:
    """Serialise a system_admin User to a safe response dict."""
    return {
        "id":         user.id,
        "email":      user.email,
        "username":   user.username,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "full_name":  f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "role":       user.role,
        "is_active":  user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def _validate_password(password: str) -> str | None:
    """Return an error string if the password is too weak, else None."""
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if not PASSWORD_PATTERN.match(password):
        return (
            "Password must contain at least one uppercase letter, one lowercase letter, "
            "one digit, and one special character."
        )
    return None


def _active_admin_count() -> int:
    """Return the number of active system_admin accounts."""
    return User.query.filter_by(role='system_admin', is_active=True).count()


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route('/system-admins', methods=['GET'])
@role_required('system_admin')
def list_system_admins(current_user):
    """
    GET /api/system-admins
    List all system_admin users with optional search and pagination.

    Query params:
        search  — partial match on email, first_name, last_name (optional)
        active  — 'true' | 'false' | '' (optional, default: all)
        page    — page number (default: 1)
        per_page — results per page (default: 20, max: 100)
    """
    search   = request.args.get('search', '').strip()
    active   = request.args.get('active', '').strip().lower()
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(1, int(request.args.get('per_page', 20))))

    query = User.query.filter_by(role='system_admin')

    if search:
        like = f'%{search}%'
        query = query.filter(
            db.or_(
                User.email.ilike(like),
                User.first_name.ilike(like),
                User.last_name.ilike(like),
                User.username.ilike(like),
            )
        )

    if active == 'true':
        query = query.filter_by(is_active=True)
    elif active == 'false':
        query = query.filter_by(is_active=False)

    query = query.order_by(User.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "admins": [_admin_to_dict(u) for u in paginated.items],
        "pagination": {
            "total":    paginated.total,
            "pages":    paginated.pages,
            "page":     paginated.page,
            "per_page": paginated.per_page,
        },
    }), 200


@bp.route('/system-admins', methods=['POST'])
@role_required('system_admin')
@limiter.limit("10 per hour")
def create_system_admin(current_user):
    """
    POST /api/system-admins
    Create a new system_admin user.

    Request body:
        {
            "email":      "jane@grantthrive.com",   (required)
            "first_name": "Jane",                   (required)
            "last_name":  "Smith",                  (required)
            "password":   "Str0ng!Pass#99",         (required, min 12 chars)
            "username":   "jane_smith"              (optional, auto-derived if omitted)
        }
    """
    data = request.get_json(silent=True) or {}

    email      = (data.get('email') or '').strip().lower()
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    password   = data.get('password') or ''
    username   = (data.get('username') or '').strip()

    # ── Validation ────────────────────────────────────────────────────────────
    errors = {}
    if not email or '@' not in email:
        errors['email'] = 'A valid email address is required.'
    if not first_name:
        errors['first_name'] = 'First name is required.'
    if not last_name:
        errors['last_name'] = 'Last name is required.'

    pwd_error = _validate_password(password)
    if pwd_error:
        errors['password'] = pwd_error

    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 422

    # ── Uniqueness checks ─────────────────────────────────────────────────────
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email address already exists."}), 409

    if not username:
        base = email.split('@')[0].replace('.', '_').replace('-', '_')
        username = base
        suffix = 1
        while User.query.filter_by(username=username).first():
            username = f"{base}_{suffix}"
            suffix += 1
    elif User.query.filter_by(username=username).first():
        return jsonify({"error": "This username is already taken."}), 409

    # ── Create user ───────────────────────────────────────────────────────────
    new_admin = User(
        email      = email,
        username   = username,
        first_name = first_name,
        last_name  = last_name,
        role       = 'system_admin',
        council_id = None,          # system_admin is never scoped to a council
        is_active  = True,
        created_at = datetime.now(timezone.utc),
    )
    new_admin.set_password(password)

    db.session.add(new_admin)
    db.session.flush()  # get the new ID before commit

    _write_audit_log(
        current_user.id,
        "system_admin.create",
        f"created system_admin user_id={new_admin.id} email={email}",
        council_id=None,
    )

    db.session.commit()

    logger.info(
        "system_admin created: new_user_id=%d email=%s by actor_id=%d",
        new_admin.id, email, current_user.id,
    )

    return jsonify({
        "message": "System admin account created successfully.",
        "admin":   _admin_to_dict(new_admin),
    }), 201


@bp.route('/system-admins/<int:admin_id>', methods=['GET'])
@role_required('system_admin')
def get_system_admin(current_user, admin_id):
    """
    GET /api/system-admins/<id>
    Retrieve a single system_admin user by ID.
    """
    user = User.query.filter_by(id=admin_id, role='system_admin').first()
    if not user:
        return jsonify({"error": "System admin not found."}), 404

    return jsonify({"admin": _admin_to_dict(user)}), 200


@bp.route('/system-admins/<int:admin_id>', methods=['PATCH'])
@role_required('system_admin')
def update_system_admin(current_user, admin_id):
    """
    PATCH /api/system-admins/<id>
    Update a system_admin user's profile or password.

    Request body (all fields optional):
        {
            "first_name": "Jane",
            "last_name":  "Smith",
            "email":      "jane@grantthrive.com",
            "password":   "NewStr0ng!Pass#99"
        }
    """
    user = User.query.filter_by(id=admin_id, role='system_admin').first()
    if not user:
        return jsonify({"error": "System admin not found."}), 404

    data    = request.get_json(silent=True) or {}
    changes = []
    errors  = {}

    # First name
    if 'first_name' in data:
        val = (data['first_name'] or '').strip()
        if not val:
            errors['first_name'] = 'First name cannot be empty.'
        else:
            user.first_name = val
            changes.append('first_name')

    # Last name
    if 'last_name' in data:
        val = (data['last_name'] or '').strip()
        if not val:
            errors['last_name'] = 'Last name cannot be empty.'
        else:
            user.last_name = val
            changes.append('last_name')

    # Email
    if 'email' in data:
        val = (data['email'] or '').strip().lower()
        if not val or '@' not in val:
            errors['email'] = 'A valid email address is required.'
        else:
            existing = User.query.filter_by(email=val).first()
            if existing and existing.id != admin_id:
                errors['email'] = 'This email address is already in use.'
            else:
                user.email = val
                changes.append('email')

    # Password
    if 'password' in data:
        pwd_error = _validate_password(data['password'])
        if pwd_error:
            errors['password'] = pwd_error
        else:
            user.set_password(data['password'])
            changes.append('password')

    if errors:
        return jsonify({"error": "Validation failed.", "fields": errors}), 422

    if not changes:
        return jsonify({"message": "No changes provided.", "admin": _admin_to_dict(user)}), 200

    _write_audit_log(
        current_user.id,
        "system_admin.update",
        f"updated system_admin user_id={admin_id} fields={','.join(changes)}",
        council_id=None,
    )

    db.session.commit()

    logger.info(
        "system_admin updated: user_id=%d fields=%s by actor_id=%d",
        admin_id, changes, current_user.id,
    )

    return jsonify({
        "message": "System admin account updated successfully.",
        "admin":   _admin_to_dict(user),
    }), 200


@bp.route('/system-admins/<int:admin_id>', methods=['DELETE'])
@role_required('system_admin')
def deactivate_system_admin(current_user, admin_id):
    """
    DELETE /api/system-admins/<id>
    Soft-deactivate a system_admin user (sets is_active = False).

    Guards:
    - Cannot deactivate your own account.
    - Cannot deactivate the last active system_admin.
    """
    user = User.query.filter_by(id=admin_id, role='system_admin').first()
    if not user:
        return jsonify({"error": "System admin not found."}), 404

    if user.id == current_user.id:
        return jsonify({"error": "You cannot deactivate your own account."}), 403

    if not user.is_active:
        return jsonify({"error": "This account is already inactive."}), 409

    if _active_admin_count() <= 1:
        return jsonify({
            "error": "Cannot deactivate the last active system admin. "
                     "Create another system admin first."
        }), 409

    user.is_active = False

    _write_audit_log(
        current_user.id,
        "system_admin.deactivate",
        f"deactivated system_admin user_id={admin_id} email={user.email}",
        council_id=None,
    )

    db.session.commit()

    logger.info(
        "system_admin deactivated: user_id=%d by actor_id=%d",
        admin_id, current_user.id,
    )

    return jsonify({"message": "System admin account deactivated."}), 200


@bp.route('/system-admins/<int:admin_id>/restore', methods=['POST'])
@role_required('system_admin')
def restore_system_admin(current_user, admin_id):
    """
    POST /api/system-admins/<id>/restore
    Reactivate a previously deactivated system_admin user.
    """
    user = User.query.filter_by(id=admin_id, role='system_admin').first()
    if not user:
        return jsonify({"error": "System admin not found."}), 404

    if user.is_active:
        return jsonify({"error": "This account is already active."}), 409

    user.is_active = True

    _write_audit_log(
        current_user.id,
        "system_admin.restore",
        f"restored system_admin user_id={admin_id} email={user.email}",
        council_id=None,
    )

    db.session.commit()

    logger.info(
        "system_admin restored: user_id=%d by actor_id=%d",
        admin_id, current_user.id,
    )

    return jsonify({
        "message": "System admin account reactivated.",
        "admin":   _admin_to_dict(user),
    }), 200


# ── Council Admin Approval Endpoints ─────────────────────────────────────────
# These endpoints are consumed by the AdminApprovalDashboard in the React
# System Admin panel.  They allow system_admin users to review, approve, or
# reject self-registered council_admin accounts that are pending approval.

def _pending_user_to_dict(user: User) -> dict:
    """Serialise a pending user to the shape expected by AdminApprovalDashboard."""
    from datetime import datetime, timezone
    days_pending = 0
    if user.created_at:
        delta = datetime.now(timezone.utc) - user.created_at.replace(tzinfo=timezone.utc)
        days_pending = delta.days
    return {
        "id":               user.id,
        "email":            user.email,
        "first_name":       user.first_name,
        "last_name":        user.last_name,
        "full_name":        f"{user.first_name} {user.last_name}",
        "role":             user.role,
        "phone":            user.phone,
        # 'organisation' stored internally; expose as 'organization_name' for the dashboard
        "organisation":     user.organisation,
        "organization_name": user.organisation,
        "position":         getattr(user, 'position', None),
        "department":       getattr(user, 'department', None),
        "subdomain":        getattr(user, 'requested_subdomain', None),
        "is_active":        user.is_active,
        "is_approved":      user.is_approved,
        "created_at":       user.created_at.isoformat() if user.created_at else None,
        "days_pending":     days_pending,
    }


@bp.route('/admin/users/pending', methods=['GET'])
@role_required('system_admin')
def get_pending_users(current_user):
    """
    GET /api/admin/users/pending
    Return all users awaiting system_admin approval (is_active=False, is_approved=False).
    Ordered by registration date, oldest first.
    """
    pending = (
        User.query
        .filter_by(is_active=False, is_approved=False)
        .filter(User.role.in_(['council_admin', 'council_staff',
                                'community_member', 'professional_consultant']))
        .order_by(User.created_at.asc())
        .all()
    )
    return jsonify({
        "pending_users": [_pending_user_to_dict(u) for u in pending],
        "count":         len(pending),
    }), 200


@bp.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@role_required('system_admin')
def approve_pending_user(current_user, user_id):
    """
    POST /api/admin/users/<id>/approve
    Approve a pending user registration.  Sets is_active=True, is_approved=True.
    For council_admin registrations, also creates the Council record if it does
    not already exist and links the user to it.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    if user.is_active and user.is_approved:
        return jsonify({"error": "User is already approved and active."}), 409

    # ── For council_admin: create the Council record if needed ────────────────
    if user.role == 'council_admin' and not user.council_id:
        from app.models import Council
        from datetime import timedelta

        # Derive subdomain from requested_subdomain or organisation name
        raw_subdomain = getattr(user, 'requested_subdomain', None)
        if not raw_subdomain and user.organisation:
            raw_subdomain = Council.make_subdomain(user.organisation)
        elif not raw_subdomain:
            # Fall back to email local-part
            raw_subdomain = Council.make_subdomain(user.email.split('@')[0])

        # Block approval if the requested subdomain is already taken.
        # The registrant must choose a different subdomain before this
        # account can be approved.  This prevents silent URL collisions
        # between same-name councils in different states.
        subdomain = raw_subdomain
        if (
            Council.query.filter_by(subdomain=subdomain).first()
            or Council.query.filter_by(slug=subdomain).first()
        ):
            logger.warning(
                "Approval blocked: subdomain '%s' already in use (user_id=%d)",
                subdomain, user_id,
            )
            return jsonify({
                "error": (
                    f"The requested subdomain \u2018{subdomain}\u2019 is already in use by another council. "
                    "Please contact the applicant to choose a different subdomain, "
                    "then update their requested subdomain before approving."
                ),
                "conflict": "subdomain_taken",
                "subdomain": subdomain,
            }), 409

        council = Council(
            name          = user.organisation or f"{user.first_name} {user.last_name}'s Council",
            subdomain     = subdomain,
            slug          = subdomain,
            plan          = 'trial',
            is_active     = True,
            trial_ends_at = datetime.now(timezone.utc) + timedelta(days=14),
            contact_email = user.email,
            contact_phone = user.phone,
        )
        db.session.add(council)
        db.session.flush()
        user.council_id = council.id
        logger.info(
            "Council created on approval: council_id=%d subdomain=%s for user_id=%d",
            council.id, subdomain, user.id,
        )

    user.is_active   = True
    user.is_approved = True

    _write_audit_log(
        current_user.id,
        "admin.approve_user",
        f"approved user_id={user_id} role={user.role}",
        council_id=user.council_id,
    )
    db.session.commit()

    logger.info("User approved: user_id=%d by actor_id=%d", user_id, current_user.id)

    # Send welcome email (best-effort)
    try:
        from app.common import email_service
        email_service.send_welcome_getting_started(user.email, user.first_name)
    except Exception as _e:
        logger.warning("Approval welcome email failed for user_id=%d: %s", user_id, _e)

    return jsonify({
        "message": "User approved successfully.",
        "user":    _pending_user_to_dict(user),
    }), 200


@bp.route('/admin/users/<int:user_id>/reject', methods=['POST'])
@role_required('system_admin')
def reject_pending_user(current_user, user_id):
    """
    POST /api/admin/users/<id>/reject
    Reject a pending user registration.  The user record is deleted and the
    applicant is notified by email with the optional rejection reason.
    """
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404

    data   = request.get_json(silent=True) or {}
    reason = (data.get("reason") or "").strip() or None

    # Capture details before deletion for logging / email
    email      = user.email
    first_name = user.first_name
    role       = user.role

    _write_audit_log(
        current_user.id,
        "admin.reject_user",
        f"rejected user_id={user_id} role={role} reason={reason!r}",
        council_id=user.council_id,
    )

    db.session.delete(user)
    db.session.commit()

    logger.info("User rejected: user_id=%d by actor_id=%d", user_id, current_user.id)

    # Notify the applicant (best-effort)
    try:
        from app.common import email_service
        from app.common.email_service import send_email
        subject = "Your GrantThrive registration could not be approved"
        body_lines = [
            f"<p>Hi {first_name},</p>",
            "<p>Thank you for registering with GrantThrive. Unfortunately, we were unable "
            "to approve your account at this time.</p>",
        ]
        if reason:
            body_lines.append(f"<p><strong>Reason:</strong> {reason}</p>")
        body_lines.append(
            "<p>If you believe this is an error, please contact "
            "<a href='mailto:support@grantthrive.com.au'>support@grantthrive.com.au</a>.</p>"
        )
        send_email(email, subject, "".join(body_lines))
    except Exception as _e:
        logger.warning("Rejection email failed for user_id=%d: %s", user_id, _e)

    return jsonify({"message": "Registration rejected and applicant notified."}), 200


@bp.route('/admin/users/<int:user_id>/subdomain', methods=['PATCH'])
@role_required('system_admin')
def update_pending_user_subdomain(current_user, user_id):
    """
    PATCH /api/admin/users/<id>/subdomain
    Allow a system admin to update the requested_subdomain on a pending
    council_admin registration before approving it.  This is used to resolve
    subdomain conflicts (e.g. two councils with the same name in different states).

    Body: { "subdomain": "campbelltown-sa" }
    Returns: 200 { "message": "...", "subdomain": "campbelltown-sa" }
             409 if the new subdomain is also already taken
             400 if the subdomain fails format validation
    """
    from app.models import Council
    import re as _re

    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found."}), 404
    if user.role != 'council_admin':
        return jsonify({"error": "Only council_admin registrations have a subdomain."}), 400

    data = request.get_json(silent=True) or {}
    new_sub = (data.get("subdomain") or "").strip().lower()
    new_sub = _re.sub(r'[^a-z0-9-]', '', new_sub)

    if not new_sub or not _re.match(r'^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$', new_sub):
        return jsonify({
            "error": (
                "Subdomain must be 3–64 characters, contain only lowercase letters, "
                "numbers, and hyphens, and must not start or end with a hyphen."
            )
        }), 400

    reserved = {
        'www', 'app', 'admin', 'api', 'map', 'roi',
        'staging', 'dev', 'test', 'mail', 'smtp',
        'grantthrive', 'support', 'help', 'status',
    }
    if new_sub in reserved:
        return jsonify({"error": f'"{new_sub}" is a reserved subdomain and cannot be used.'}), 400

    if (
        Council.query.filter_by(subdomain=new_sub).first()
        or Council.query.filter_by(slug=new_sub).first()
    ):
        return jsonify({
            "error": f"The subdomain \u2018{new_sub}\u2019 is already in use. Please choose a different one.",
            "conflict": "subdomain_taken",
        }), 409

    old_sub = user.requested_subdomain
    user.requested_subdomain = new_sub
    _write_audit_log(
        current_user.id,
        "admin.update_user_subdomain",
        f"updated requested_subdomain for user_id={user_id}: {old_sub!r} → {new_sub!r}",
        council_id=user.council_id,
    )
    db.session.commit()
    logger.info(
        "Subdomain updated for user_id=%d: %r → %r by actor_id=%d",
        user_id, old_sub, new_sub, current_user.id,
    )
    return jsonify({
        "message": f"Subdomain updated to \u2018{new_sub}\u2019. You can now approve the registration.",
        "subdomain": new_sub,
    }), 200


# ── Twilio / SMS Configuration ────────────────────────────────────────────────
#
# These endpoints allow GrantThrive system admins to configure the centralised
# Twilio account that powers SMS notifications for all council clients.
#
# Routes
# ------
#   GET    /api/system/twilio-config        — Read current config (tokens masked)
#   PUT    /api/system/twilio-config        — Save / update config
#   POST   /api/system/twilio-config/test   — Send a test SMS to verify credentials
#   DELETE /api/system/twilio-config        — Clear all Twilio credentials
#
# Security: all routes require system_admin role.
# Sensitive values (auth token) are stored encrypted in the system_config table.

_TWILIO_KEYS = {
    'twilio_account_sid':            False,   # not sensitive — visible in Twilio console
    'twilio_auth_token':             True,    # sensitive — encrypted at rest
    'twilio_messaging_service_sid':  False,   # not sensitive
    'twilio_from_number':            False,   # fallback sender number
    'twilio_enabled':                False,   # 'true' / 'false' toggle
}


def _mask(value):
    """Return a masked version of a credential for display (last 4 chars visible)."""
    if not value:
        return None
    if len(value) <= 4:
        return '****'
    return '\u2022' * (len(value) - 4) + value[-4:]


@bp.route('/system/twilio-config', methods=['GET'])
@role_required('system_admin')
def get_twilio_config(current_user):
    """GET /api/system/twilio-config — Returns current Twilio config. Sensitive values masked."""
    from app.models import SystemConfig
    config = {}
    for key, sensitive in _TWILIO_KEYS.items():
        raw = SystemConfig.get(key)
        config[key] = _mask(raw) if sensitive else raw
    config['is_configured'] = bool(
        SystemConfig.get('twilio_account_sid') and
        SystemConfig.get('twilio_auth_token') and
        (SystemConfig.get('twilio_messaging_service_sid') or SystemConfig.get('twilio_from_number'))
    )
    config['is_enabled'] = SystemConfig.get('twilio_enabled') == 'true'
    return jsonify({'config': config}), 200


@bp.route('/system/twilio-config', methods=['PUT'])
@role_required('system_admin')
def save_twilio_config(current_user):
    """PUT /api/system/twilio-config — Save or update Twilio credentials."""
    from app.models import SystemConfig
    data = request.get_json(silent=True) or {}
    allowed = set(_TWILIO_KEYS.keys())
    updated = []
    for key in allowed:
        if key not in data:
            continue
        value = str(data[key]).strip() if data[key] is not None else ''
        sensitive = _TWILIO_KEYS.get(key, False)
        if value == '':
            SystemConfig.delete(key)
        else:
            SystemConfig.set(key, value, sensitive=sensitive,
                             updated_by=f'{current_user.first_name} {current_user.last_name}')
        updated.append(key)
    _write_audit_log(
        current_user.id,
        'admin.update_twilio_config',
        f'Updated Twilio config keys: {", ".join(updated)}',
    )
    logger.info('Twilio config updated by system_admin user_id=%d', current_user.id)
    return jsonify({'message': 'Twilio configuration saved successfully.', 'updated': updated}), 200


@bp.route('/system/twilio-config/test', methods=['POST'])
@role_required('system_admin')
def test_twilio_config(current_user):
    """POST /api/system/twilio-config/test — Send a test SMS to verify credentials."""
    from app.models import SystemConfig
    data = request.get_json(silent=True) or {}
    to_number = (data.get('to') or '').strip()
    if not to_number:
        return jsonify({'error': 'A destination phone number is required.'}), 400
    account_sid = SystemConfig.get('twilio_account_sid')
    auth_token  = SystemConfig.get('twilio_auth_token')
    if not account_sid or not auth_token:
        return jsonify({'error': 'Twilio credentials are not configured. Save your Account SID and Auth Token first.'}), 422
    messaging_sid = SystemConfig.get('twilio_messaging_service_sid')
    from_number   = SystemConfig.get('twilio_from_number')
    if not messaging_sid and not from_number:
        return jsonify({'error': 'A Messaging Service SID or From number is required.'}), 422
    try:
        from twilio.rest import Client as TwilioClient
        from twilio.base.exceptions import TwilioRestException
        client = TwilioClient(account_sid, auth_token)
        kwargs = {
            'body': 'This is a test SMS from GrantThrive. Your Twilio integration is working correctly.',
            'to':   to_number,
        }
        if messaging_sid:
            kwargs['messaging_service_sid'] = messaging_sid
        else:
            kwargs['from_'] = from_number
        msg = client.messages.create(**kwargs)
        _write_audit_log(current_user.id, 'admin.test_twilio_config',
                         f'Test SMS sent to {to_number}, Twilio SID={msg.sid}')
        return jsonify({'message': f'Test SMS sent successfully. Twilio message SID: {msg.sid}'}), 200
    except Exception as e:
        logger.warning('Twilio test SMS failed: %s', e)
        return jsonify({'error': str(e)}), 422


@bp.route('/system/twilio-config', methods=['DELETE'])
@role_required('system_admin')
def clear_twilio_config(current_user):
    """DELETE /api/system/twilio-config — Remove all stored Twilio credentials."""
    from app.models import SystemConfig
    for key in _TWILIO_KEYS:
        SystemConfig.delete(key)
    _write_audit_log(current_user.id, 'admin.clear_twilio_config', 'All Twilio credentials cleared.')
    logger.info('Twilio config cleared by system_admin user_id=%d', current_user.id)
    return jsonify({'message': 'Twilio configuration cleared.'}), 200
