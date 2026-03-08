"""
GrantThrive — Council (Tenant) Management API
==============================================
REST endpoints for provisioning and managing council tenants.

All write operations require the ``system_admin`` role.
Read operations for a single council are also available to that council's
``council_admin`` users.

Endpoints:
  GET    /api/councils                — List all councils (system_admin only)
  POST   /api/councils                — Create a new council (system_admin only)
  GET    /api/councils/<id>           — Get a council's profile
  PATCH  /api/councils/<id>           — Update a council's profile
  DELETE /api/councils/<id>           — Deactivate a council (soft delete)
  GET    /api/councils/<id>/users     — List users belonging to a council
  POST   /api/councils/<id>/users     — Provision a council_admin user
  GET    /api/councils/resolve        — Resolve subdomain → council (used by frontend)
"""

import logging
import re
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify

from app import db
from app.models import Council, User
from app.auth.routes import token_required, role_required
from app.tenancy.middleware import get_current_council
from app.common.password import hash_password
logger = logging.getLogger(__name__)

councils_bp = Blueprint('councils', __name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_subdomain(subdomain: str) -> str | None:
    """Return an error string if the subdomain is invalid, else None."""
    if not subdomain:
        return 'Subdomain is required.'
    if not re.match(r'^[a-z0-9][a-z0-9-]{1,62}[a-z0-9]$', subdomain):
        return (
            'Subdomain must be 3–64 characters, contain only lowercase letters, '
            'numbers, and hyphens, and must not start or end with a hyphen.'
        )
    reserved = {
        'www', 'app', 'admin', 'api', 'map', 'roi',
        'staging', 'dev', 'test', 'mail', 'smtp',
        'grantthrive', 'support', 'help', 'status',
    }
    if subdomain in reserved:
        return f'"{subdomain}" is a reserved subdomain and cannot be used.'
    return None


# ── Routes ────────────────────────────────────────────────────────────────────

@councils_bp.route('/councils/check-subdomain', methods=['GET'])
def check_subdomain():
    """
    Public endpoint — check whether a subdomain is available.

    GET /api/councils/check-subdomain?subdomain=chb

    Returns:
        200  { "available": true,  "subdomain": "chb" }
        200  { "available": false, "subdomain": "chb",  "reason": "already in use" }
        400  { "available": false, "subdomain": "chb",  "reason": "<validation message>" }
    """
    raw = (request.args.get('subdomain') or '').strip().lower()

    # Sanitise to valid characters before validation so the preview JS
    # can send partially-typed values without triggering noisy errors.
    import re as _re
    sanitised = _re.sub(r'[^a-z0-9-]', '', raw)

    err = _validate_subdomain(sanitised)
    if err:
        return jsonify({'available': False, 'subdomain': sanitised, 'reason': err}), 400

    taken = Council.query.filter_by(subdomain=sanitised).first() is not None
    if taken:
        return jsonify({'available': False, 'subdomain': sanitised, 'reason': 'That subdomain is already in use.'}), 200

    return jsonify({'available': True, 'subdomain': sanitised}), 200


@councils_bp.route('/councils', methods=['GET'])
@role_required('system_admin')
def list_councils(current_user):
    """List all councils. System admin only."""
    page     = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 25, type=int), 100)
    search   = request.args.get('q', '').strip()
    state    = request.args.get('state', '').strip()
    plan     = request.args.get('plan', '').strip()
    active   = request.args.get('active', None)

    q = Council.query

    if search:
        like = f'%{search}%'
        q = q.filter(
            db.or_(
                Council.name.ilike(like),
                Council.subdomain.ilike(like),
                Council.lga_code.ilike(like),
            )
        )
    if state:
        q = q.filter(Council.state.ilike(state))
    if plan:
        q = q.filter(Council.plan == plan)
    if active is not None:
        q = q.filter(Council.is_active == (active.lower() == 'true'))

    q = q.order_by(Council.name)
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'councils':   [c.to_dict() for c in pagination.items],
        'total':      pagination.total,
        'page':       pagination.page,
        'per_page':   pagination.per_page,
        'pages':      pagination.pages,
    }), 200


@councils_bp.route('/councils', methods=['POST'])
@role_required('system_admin')
def create_council(current_user):
    """
    Provision a new council tenant.

    Request body:
        {
          "name":           "City of Melbourne",
          "subdomain":      "cityofmelbourne",       (optional — auto-derived from name)
          "state":          "VIC",
          "lga_code":       "24600",                 (optional)
          "plan":           "starter",               (optional, default: starter)
          "contact_email":  "grants@melbourne.vic.gov.au",
          "contact_phone":  "+61 3 9658 9658",       (optional)
          "website_url":    "https://www.melbourne.vic.gov.au", (optional)
          "primary_colour": "#15803d",               (optional)
          "admin_email":    "admin@melbourne.vic.gov.au",   (optional — creates council_admin)
          "admin_first_name": "Sarah",               (required if admin_email provided)
          "admin_last_name":  "Johnson",             (required if admin_email provided)
          "admin_password":   "...",                 (required if admin_email provided)
        }
    """
    data = request.get_json(silent=True) or {}

    name  = (data.get('name') or '').strip()
    state = (data.get('state') or '').strip().upper()

    if not name:
        return jsonify({'error': 'Council name is required.'}), 400
    if not state:
        return jsonify({'error': 'State is required.'}), 400

    # Derive subdomain if not provided
    subdomain = (data.get('subdomain') or Council.make_subdomain(name)).strip().lower()
    slug      = Council.make_slug(name)

    err = _validate_subdomain(subdomain)
    if err:
        return jsonify({'error': err}), 400

    if Council.query.filter_by(subdomain=subdomain).first():
        return jsonify({'error': f'Subdomain "{subdomain}" is already in use.'}), 409

    # ── Plan validation ──────────────────────────────────────────────────────
    from app.common.plans import PLAN_LIMITS, plan_entitlements
    VALID_PLANS = {'small', 'medium', 'large', 'trial'}
    requested_plan = data.get('plan', 'small').lower()
    if requested_plan not in VALID_PLANS:
        return jsonify({'error': f'Invalid plan "{requested_plan}". Must be one of: small, medium, large, trial.'}), 400

    council = Council(
        name             = name,
        subdomain        = subdomain,
        slug             = slug,
        state            = state,
        lga_code         = (data.get('lga_code') or '').strip() or None,
        plan             = requested_plan,
        contact_email    = (data.get('contact_email') or '').strip() or None,
        contact_phone    = (data.get('contact_phone') or '').strip() or None,
        website_url      = (data.get('website_url') or '').strip() or None,
        primary_colour   = data.get('primary_colour', '#15803d'),
        secondary_colour = data.get('secondary_colour', '#166534'),
        is_active        = True,
        created_by       = current_user.id,
    )
    db.session.add(council)
    db.session.flush()  # Get council.id before committing

    # Optionally provision a council_admin user in the same transaction
    admin_user = None
    admin_email = (data.get('admin_email') or '').strip().lower()
    if admin_email:
        admin_first = (data.get('admin_first_name') or '').strip()
        admin_last  = (data.get('admin_last_name') or '').strip()
        admin_pass  = data.get('admin_password') or ''

        if not all([admin_first, admin_last, admin_pass]):
            db.session.rollback()
            return jsonify({
                'error': 'admin_first_name, admin_last_name, and admin_password are '
                         'required when admin_email is provided.'
            }), 400

        if len(admin_pass) < 10:
            db.session.rollback()
            return jsonify({'error': 'Admin password must be at least 10 characters.'}), 400

        if User.query.filter_by(email=admin_email).first():
            db.session.rollback()
            return jsonify({'error': f'A user with email "{admin_email}" already exists.'}), 409

        base_username = admin_email.split('@')[0].replace('.', '_')
        username = base_username
        counter  = 1
        while User.query.filter_by(username=username).first():
            username = f'{base_username}{counter}'
            counter += 1

        admin_user = User(
            username      = username,
            email         = admin_email,
            password_hash = hash_password(admin_pass),
            first_name    = admin_first,
            last_name     = admin_last,
            role          = 'council_admin',
            council_id    = council.id,
            is_active     = True,
        )
        db.session.add(admin_user)

    db.session.commit()

    logger.info(
        "Council provisioned: id=%d subdomain=%s by system_admin user_id=%d",
        council.id, council.subdomain, current_user.id,
    )

    response = {
        'message':      f'Council "{name}" provisioned successfully.',
        'council':      council.to_dict(),
        'entitlements': plan_entitlements(requested_plan),
    }
    if admin_user:
        response['admin_user'] = {
            'id':    admin_user.id,
            'email': admin_user.email,
            'role':  admin_user.role,
        }
    return jsonify(response), 201


@councils_bp.route('/councils/resolve', methods=['GET'])
def resolve_council():
    """
    Resolve a subdomain to a council profile.
    Used by the frontend on load to fetch branding and config for the
    current tenant.

    Query params:
        subdomain=cityofmelbourne

    Response (200):
        { "council": { ... } }

    Response (404):
        { "error": "Council not found." }
    """
    subdomain = (request.args.get('subdomain') or '').strip().lower()
    if not subdomain:
        # Fall back to Host header
        from app.tenancy.middleware import _extract_subdomain
        subdomain = _extract_subdomain(request.headers.get('Host', '')) or ''

    if not subdomain:
        return jsonify({'error': 'No subdomain provided.'}), 400

    council = Council.query.filter_by(subdomain=subdomain, is_active=True).first()
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    return jsonify({'council': council.to_dict()}), 200


@councils_bp.route('/councils/<int:council_id>', methods=['GET'])
@token_required
def get_council(current_user, council_id):
    """
    Get a council's profile.

    Accessible to:
      - system_admin (any council)
      - council_admin / council_staff (their own council only)
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    if current_user.role != 'system_admin' and current_user.council_id != council_id:
        return jsonify({'error': 'Access denied.'}), 403

    return jsonify({'council': council.to_dict()}), 200


@councils_bp.route('/councils/<int:council_id>', methods=['PATCH'])
@token_required
def update_council(current_user, council_id):
    """
    Update a council's profile.

    Accessible to:
      - system_admin (any field on any council)
      - council_admin (branding and contact fields on their own council only)
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_council  = current_user.council_id == council_id and \
                      current_user.role == 'council_admin'

    if not is_system_admin and not is_own_council:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}

    # Fields any council_admin can update
    editable_by_council_admin = {
        'contact_email', 'contact_phone', 'website_url',
        'primary_colour', 'secondary_colour', 'logo_url', 'address', 'postcode',
    }
    # Additional fields only system_admin can update
    editable_by_system_admin = editable_by_council_admin | {
        'name', 'subdomain', 'slug', 'state', 'lga_code', 'plan', 'is_active',
        'trial_ends_at', 'country',
    }

    allowed = editable_by_system_admin if is_system_admin else editable_by_council_admin

    for field in allowed:
        if field in data:
            if field == 'subdomain':
                new_sub = (data[field] or '').strip().lower()
                err = _validate_subdomain(new_sub)
                if err:
                    return jsonify({'error': err}), 400
                existing = Council.query.filter_by(subdomain=new_sub).first()
                if existing and existing.id != council_id:
                    return jsonify({'error': f'Subdomain "{new_sub}" is already in use.'}), 409
                setattr(council, field, new_sub)
            else:
                setattr(council, field, data[field])

    council.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Council updated: id=%d by user_id=%d", council_id, current_user.id)
    return jsonify({'council': council.to_dict()}), 200


@councils_bp.route('/councils/<int:council_id>', methods=['DELETE'])
@role_required('system_admin')
def deactivate_council(current_user, council_id):
    """
    Soft-delete (deactivate) a council.  Data is retained.
    System admin only.
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    council.is_active  = False
    council.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    logger.info("Council deactivated: id=%d by system_admin user_id=%d", council_id, current_user.id)
    return jsonify({'message': f'Council "{council.name}" has been deactivated.'}), 200


@councils_bp.route('/councils/<int:council_id>/users', methods=['GET'])
@token_required
def list_council_users(current_user, council_id):
    """List users belonging to a council."""
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_council  = current_user.council_id == council_id and \
                      current_user.role in ('council_admin', 'council_staff')

    if not is_system_admin and not is_own_council:
        return jsonify({'error': 'Access denied.'}), 403

    users = User.query.filter_by(council_id=council_id).order_by(User.last_name).all()
    return jsonify({
        'users': [
            {
                'id':         u.id,
                'email':      u.email,
                'full_name':  u.full_name,
                'role':       u.role,
                'is_active':  u.is_active,
                'last_login': u.last_login.isoformat() if u.last_login else None,
            }
            for u in users
        ],
        'total': len(users),
    }), 200


@councils_bp.route('/councils/<int:council_id>/users', methods=['POST'])
@role_required('system_admin')
def provision_council_user(current_user, council_id):
    """
    Provision a new user (typically council_admin) for a council.
    System admin only.

    Request body:
        {
          "email": "...", "password": "...",
          "first_name": "...", "last_name": "...",
          "role": "council_admin"
        }
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    data       = request.get_json(silent=True) or {}
    email      = (data.get('email') or '').strip().lower()
    password   = data.get('password') or ''
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    role       = data.get('role', 'council_admin')

    if not all([email, password, first_name, last_name]):
        return jsonify({'error': 'email, password, first_name, and last_name are required.'}), 400

    allowed_roles = {'council_admin', 'council_staff', 'community_member', 'professional_consultant'}
    if role not in allowed_roles:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(sorted(allowed_roles))}'}), 400

    if len(password) < 10:
        return jsonify({'error': 'Password must be at least 10 characters.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': f'A user with email "{email}" already exists.'}), 409

    base_username = email.split('@')[0].replace('.', '_')
    username = base_username
    counter  = 1
    while User.query.filter_by(username=username).first():
        username = f'{base_username}{counter}'
        counter += 1

    user = User(
        username      = username,
        email         = email,
        password_hash = hash_password(password),
        first_name    = first_name,
        last_name     = last_name,
        role          = role,
        council_id    = council_id,
        is_active     = True,
    )
    db.session.add(user)
    db.session.commit()

    logger.info(
        "User provisioned: user_id=%d role=%s council_id=%d by system_admin user_id=%d",
        user.id, role, council_id, current_user.id,
    )
    return jsonify({
        'message': f'User "{email}" provisioned for council "{council.name}".',
        'user': {
            'id':        user.id,
            'email':     user.email,
            'full_name': user.full_name,
            'role':      user.role,
        },
    }), 201


@councils_bp.route('/councils/trial', methods=['POST'])
def start_trial():
    """
    Self-serve trial onboarding endpoint — no authentication required.

    A prospective council fills out the "Start Free Trial" form on the
    marketing website or portal.  This endpoint:
      1. Validates all inputs.
      2. Creates a new Council record (plan='trial', 14-day trial_ends_at).
      3. Creates the first council_admin user with is_active=True.
      4. Returns a JWT so the user lands directly in their dashboard.
      5. Sends a welcome email (logged to console in dev).

    Request body:
        {
          "council_name":  "City of Melbourne",
          "state":         "VIC",
          "first_name":    "Sarah",
          "last_name":     "Johnson",
          "email":         "sarah@melbourne.vic.gov.au",
          "password":      "...",
          "phone":         "+61 3 9658 9658"   (optional)
        }

    Response (201):
        {
          "token":   "<jwt>",
          "user":    { ... },
          "council": { ... },
          "message": "Welcome to GrantThrive! Your 14-day trial has started."
        }
    """
    from datetime import timedelta
    from app.auth.routes import _generate_token, _user_to_dict
    from app.tenancy.email import send_trial_welcome_email
    from app.common.plans import plan_entitlements
    data         = request.get_json(silent=True) or {}
    council_name = (data.get('council_name') or '').strip()
    state        = (data.get('state') or '').strip().upper()
    first_name   = (data.get('first_name') or '').strip()
    last_name    = (data.get('last_name') or '').strip()
    email        = (data.get('email') or '').strip().lower()
    password     = data.get('password') or ''
    phone        = (data.get('phone') or '').strip() or None
    # The plan the council intends to subscribe to after the trial.
    # Stored for reference; entitlements during trial are always 'trial' limits.
    VALID_PLANS = {'small', 'medium', 'large'}
    intended_plan = (data.get('intended_plan') or 'small').lower()
    if intended_plan not in VALID_PLANS:
        intended_plan = 'small'

    # ── Validation ────────────────────────────────────────────────────────────
    errors = {}
    if not council_name:
        errors['council_name'] = 'Council name is required.'
    if not state:
        errors['state'] = 'State / region is required.'
    if not first_name:
        errors['first_name'] = 'First name is required.'
    if not last_name:
        errors['last_name'] = 'Last name is required.'
    if not email or '@' not in email:
        errors['email'] = 'A valid email address is required.'
    if len(password) < 10:
        errors['password'] = 'Password must be at least 10 characters.'
    if errors:
        return jsonify({'errors': errors}), 400

    # ── Uniqueness checks ─────────────────────────────────────────────────────
    if User.query.filter_by(email=email).first():
        return jsonify({'errors': {'email': 'An account with this email already exists.'}}), 409

    subdomain = Council.make_subdomain(council_name)
    slug      = Council.make_slug(council_name)

    # If the derived subdomain is taken, append an incrementing suffix
    original_subdomain = subdomain
    attempt = 0
    while Council.query.filter_by(subdomain=subdomain).first():
        attempt += 1
        subdomain = f'{original_subdomain}{attempt}'

    err = _validate_subdomain(subdomain)
    if err:
        return jsonify({'errors': {'council_name': err}}), 400

    # ── Create council ────────────────────────────────────────────────────────
    trial_ends = datetime.now(timezone.utc) + timedelta(days=14)
    council = Council(
        name          = council_name,
        subdomain     = subdomain,
        slug          = slug,
        state         = state,
        plan          = 'trial',
        is_active     = True,
        trial_ends_at = trial_ends,
        contact_email = email,
        contact_phone = phone,
    )
    db.session.add(council)
    db.session.flush()  # get council.id before committing

    # ── Create council_admin user ─────────────────────────────────────────────
    base_username = email.split('@')[0].replace('.', '_')
    username = base_username
    counter  = 1
    while User.query.filter_by(username=username).first():
        username = f'{base_username}{counter}'
        counter += 1

    user = User(
        username      = username,
        email         = email,
        password_hash = hash_password(password),
        first_name    = first_name,
        last_name     = last_name,
        role          = 'council_admin',
        council_id    = council.id,
        is_active     = True,
        phone         = phone,
    )
    db.session.add(user)
    db.session.commit()

    logger.info(
        "Trial started: council_id=%d subdomain=%s user_id=%d email=%s",
        council.id, council.subdomain, user.id, email,
    )

    # ── Send welcome email (non-blocking; errors are logged, not raised) ──────
    try:
        send_trial_welcome_email(
            to_email     = email,
            first_name   = first_name,
            council_name = council_name,
            portal_url   = council.portal_url(),
            trial_ends   = trial_ends,
        )
    except Exception as exc:  # pragma: no cover
        logger.warning("Welcome email failed for %s: %s", email, exc)

    # ── Issue JWT and return ──────────────────────────────────────────────────
    token = _generate_token(user)
    return jsonify({
        'token':         token,
        'user':          _user_to_dict(user),
        'council':       council.to_dict(),
        'entitlements':  plan_entitlements('trial'),
        'intended_plan': intended_plan,
        'message': (
            f'Welcome to GrantThrive, {first_name}! '
            f'Your 14-day free trial has started. '
            f'Your portal is at {council.portal_url()}.'
        ),
    }), 201


# ── Council-Admin Staff Management ───────────────────────────────────────────
# These endpoints allow a council_admin to manage their own council's staff
# without needing system_admin access.

@councils_bp.route('/councils/<int:council_id>/staff', methods=['POST'])
@token_required
def add_staff_member(current_user, council_id):
    """Council admin adds a new staff member to their council."""
    import secrets as _secrets
    from app.common.password import hash_password as _hash

    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    data       = request.get_json(silent=True) or {}
    email      = (data.get('email') or '').strip().lower()
    first_name = (data.get('first_name') or '').strip()
    last_name  = (data.get('last_name') or '').strip()
    role       = data.get('role', 'council_staff')
    supplied_pw = data.get('password')
    password   = supplied_pw or _secrets.token_urlsafe(12)

    if not all([email, first_name, last_name]):
        return jsonify({'error': 'email, first_name, and last_name are required.'}), 400
    if role not in {'council_staff', 'council_admin'}:
        return jsonify({'error': 'Role must be council_staff or council_admin.'}), 400
    if len(password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({'error': f'A user with email "{email}" already exists.'}), 409

    base_username = email.split('@')[0].replace('.', '_')
    username = base_username
    counter  = 1
    while User.query.filter_by(username=username).first():
        username = f'{base_username}{counter}'
        counter += 1

    user = User(
        username      = username,
        email         = email,
        password_hash = _hash(password),
        first_name    = first_name,
        last_name     = last_name,
        role          = role,
        council_id    = council_id,
        is_active     = True,
    )
    db.session.add(user)
    db.session.commit()

    logger.info("Staff added: user_id=%d role=%s council_id=%d by user_id=%d",
                user.id, role, council_id, current_user.id)

    resp = {
        'message': f'Staff member "{email}" added to {council.name}.',
        'user': {
            'id':        user.id,
            'email':     user.email,
            'full_name': user.full_name,
            'role':      user.role,
            'is_active': user.is_active,
        },
    }
    if not supplied_pw:
        resp['temporary_password'] = password
    return jsonify(resp), 201


@councils_bp.route('/councils/<int:council_id>/staff/<int:user_id>', methods=['PATCH'])
@token_required
def update_staff_member(current_user, council_id, user_id):
    """Update a staff member's details (role, active status, name)."""
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    user = db.session.get(User, user_id)
    if not user or user.council_id != council_id:
        return jsonify({'error': 'Staff member not found in this council.'}), 404

    data = request.get_json(silent=True) or {}
    if 'first_name' in data:
        user.first_name = data['first_name'].strip()
    if 'last_name' in data:
        user.last_name = data['last_name'].strip()
    if 'role' in data:
        if data['role'] not in {'council_staff', 'council_admin'}:
            return jsonify({'error': 'Role must be council_staff or council_admin.'}), 400
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])

    db.session.commit()
    logger.info("Staff updated: user_id=%d by user_id=%d", user_id, current_user.id)
    return jsonify({
        'message': 'Staff member updated.',
        'user': {
            'id':        user.id,
            'email':     user.email,
            'full_name': user.full_name,
            'role':      user.role,
            'is_active': user.is_active,
        },
    }), 200


@councils_bp.route('/councils/<int:council_id>/staff/<int:user_id>/reset-password',
                   methods=['POST'])
@token_required
def reset_staff_password(current_user, council_id, user_id):
    """Reset a staff member's password. Council admin or self."""
    from app.common.password import hash_password as _hash

    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    is_self         = current_user.id == user_id

    if not is_system_admin and not is_own_admin and not is_self:
        return jsonify({'error': 'Access denied.'}), 403

    user = db.session.get(User, user_id)
    if not user or user.council_id != council_id:
        return jsonify({'error': 'Staff member not found in this council.'}), 404

    data         = request.get_json(silent=True) or {}
    new_password = data.get('new_password') or ''
    if len(new_password) < 8:
        return jsonify({'error': 'Password must be at least 8 characters.'}), 400

    user.password_hash = _hash(new_password)
    db.session.commit()
    logger.info("Password reset: user_id=%d by user_id=%d", user_id, current_user.id)
    return jsonify({'message': 'Password has been reset successfully.'}), 200


@councils_bp.route('/councils/<int:council_id>/billing', methods=['GET'])
@token_required
def get_billing_info(current_user, council_id):
    """Return billing / subscription information for a council."""
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    from app.common.plans import get_live_plan_pricing, plan_entitlements
    plan_key  = council.plan or 'trial'
    pricing   = get_live_plan_pricing()
    plan_data = pricing.get(plan_key, {})

    return jsonify({
        'council_id':    council.id,
        'council_name':  council.name,
        'plan':          plan_key,
        'is_active':     council.is_active,
        'trial_ends_at': (
            council.trial_ends_at.isoformat() if council.trial_ends_at else None
        ),
        'billing': {
            'monthly_price_aud': plan_data.get('monthly_price_aud'),
            'annual_price_aud':  plan_data.get('annual_price_aud'),
            'addon_voting_aud':  plan_data.get('addon_voting_aud'),
            'addon_mapping_aud': plan_data.get('addon_mapping_aud'),
        },
        'entitlements': plan_entitlements(plan_key),
    }), 200
