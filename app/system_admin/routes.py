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
from werkzeug.security import generate_password_hash

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
