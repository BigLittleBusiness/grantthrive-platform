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

    # ── Notifications: staff added email + in-app notification ──
    try:
        from app.common.notifications import notify
        from app.common import email_service
        notify(
            user_id=user.id,
            ntype='staff_added',
            title=f'You have been added to {council.name}',
            message=f'A Council Administrator has added you to {council.name} as {role.replace("_", " ").title()}.',
            link='portal/council/dashboard',
            send_email_fn=lambda: email_service.send_staff_added(
                email, first_name, council.name, role, password
            ),
        )
    except Exception as _ne:
        logger.warning("Staff added notification failed: %s", _ne)

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
    plan_key = council.plan or 'trial'
    # get_live_plan_pricing(plan_key) requires a plan_key argument.
    # 'trial' is not a paid plan so pricing fields will be None/absent.
    pricing = get_live_plan_pricing(plan_key) if plan_key != 'trial' else {}

    # ── SMS add-on cost ────────────────────────────────────────────────────────
    # Look up the council's active SMS tier (if any) and include its monthly
    # price so the frontend can display a correct combined total.
    sms_monthly_cents = None
    sms_annual_cents  = None
    sms_tier_name     = None
    if council.addon_sms and council.sms_tier and council.sms_tier in SMS_TIERS:
        sms_tier_data     = SMS_TIERS[council.sms_tier]
        sms_monthly_cents = sms_tier_data['price_aud_cents']
        sms_annual_cents  = sms_tier_data['price_aud_cents'] * 12
        sms_tier_name     = sms_tier_data['name']

    # ── Combined totals ────────────────────────────────────────────────────────
    base_monthly = pricing.get('monthly_price_aud_cents') or 0
    base_annual  = pricing.get('annual_price_aud_cents')  or 0
    addon_voting   = pricing.get('addon_community_voting_cents') or 0
    addon_mapping  = pricing.get('addon_grant_mapping_cents')    or 0
    # Only count voting/mapping add-ons if the council has them enabled
    voting_cost  = addon_voting  if council.addon_community_voting else 0
    mapping_cost = addon_mapping if council.addon_grant_mapping    else 0
    sms_cost     = sms_monthly_cents or 0

    total_monthly_cents = base_monthly + voting_cost + mapping_cost + sms_cost
    total_annual_cents  = base_annual  + (voting_cost * 12) + (mapping_cost * 12) + (sms_annual_cents or 0)

    return jsonify({
        'council_id':    council.id,
        'council_name':  council.name,
        'plan':          plan_key,
        'is_active':     council.is_active,
        'trial_ends_at': (
            council.trial_ends_at.isoformat() if council.trial_ends_at else None
        ),
        # Pricing values in AUD cents — frontend divides by 100 for display.
        'billing': {
            'monthly_price_aud_cents':  pricing.get('monthly_price_aud_cents'),
            'annual_price_aud_cents':   pricing.get('annual_price_aud_cents'),
            'addon_voting_cents':       pricing.get('addon_community_voting_cents'),
            'addon_mapping_cents':      pricing.get('addon_grant_mapping_cents'),
            # SMS add-on (None when not active)
            'addon_sms_monthly_cents':  sms_monthly_cents,
            'addon_sms_annual_cents':   sms_annual_cents,
            'addon_sms_tier_name':      sms_tier_name,
            # Combined totals across all active charges
            'total_monthly_cents':      total_monthly_cents if plan_key != 'trial' else None,
            'total_annual_cents':       total_annual_cents  if plan_key != 'trial' else None,
        },
        # Council contact details (editable via PATCH /api/councils/<id>)
        'council': {
            'contact_email': council.contact_email,
            'contact_phone': council.contact_phone,
            'website_url':   council.website_url,
        },
        'entitlements': plan_entitlements(plan_key),
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Council-level staff approval endpoints
# These allow a council_admin to list, approve, and reject pending staff
# accounts that are in the approval queue (is_active=False, is_approved=False)
# for their council.
# ─────────────────────────────────────────────────────────────────────────────

@councils_bp.route('/councils/<int:council_id>/staff/pending', methods=['GET'])
@token_required
def list_pending_staff(current_user, council_id):
    """
    GET /api/councils/<id>/staff/pending
    Return all staff accounts for this council that are awaiting approval
    (is_active=False, is_approved=False).
    Accessible by: council_admin (own council), system_admin.
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    pending = (
        User.query
        .filter_by(council_id=council_id, is_active=False, is_approved=False)
        .filter(User.role.in_(['council_staff', 'council_admin']))
        .order_by(User.created_at.asc())
        .all()
    )
    return jsonify({
        'pending_staff': [
            {
                'id':         u.id,
                'email':      u.email,
                'full_name':  u.full_name,
                'first_name': u.first_name,
                'last_name':  u.last_name,
                'role':       u.role,
                'position':   getattr(u, 'position', None),
                'department': getattr(u, 'department', None),
                'phone':      getattr(u, 'phone', None),
                'created_at': u.created_at.isoformat() if getattr(u, 'created_at', None) else None,
            }
            for u in pending
        ],
        'count': len(pending),
    }), 200


@councils_bp.route('/councils/<int:council_id>/staff/<int:user_id>/approve', methods=['POST'])
@token_required
def approve_staff_member(current_user, council_id, user_id):
    """
    POST /api/councils/<id>/staff/<user_id>/approve
    Approve a pending staff account, setting is_active=True, is_approved=True.
    Accessible by: council_admin (own council), system_admin.
    """
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
    if user.is_active and user.is_approved:
        return jsonify({'error': 'Staff member is already approved and active.'}), 409

    user.is_active   = True
    user.is_approved = True
    db.session.commit()

    logger.info(
        "Staff approved: user_id=%d council_id=%d by actor_id=%d",
        user_id, council_id, current_user.id,
    )

    # Notify the staff member (best-effort)
    try:
        from app.common.notifications import notify
        from app.common import email_service
        notify(
            user_id=user.id,
            ntype='account_approved',
            title='Your account has been approved',
            message=f'Your account for {council.name} has been approved. You can now log in.',
            link='portal/council/dashboard',
            send_email_fn=lambda: email_service.send_welcome_getting_started(
                user.email, user.first_name
            ),
        )
    except Exception as _ne:
        logger.warning("Staff approval notification failed for user_id=%d: %s", user_id, _ne)

    return jsonify({
        'message': f'Staff member "{user.email}" approved and activated.',
        'user': {
            'id':        user.id,
            'email':     user.email,
            'full_name': user.full_name,
            'role':      user.role,
            'is_active': user.is_active,
        },
    }), 200


@councils_bp.route('/councils/<int:council_id>/staff/<int:user_id>/reject', methods=['POST'])
@token_required
def reject_staff_member(current_user, council_id, user_id):
    """
    POST /api/councils/<id>/staff/<user_id>/reject
    Reject a pending staff account. Deletes the user record and notifies them.
    Accessible by: council_admin (own council), system_admin.
    Body (optional): { "reason": "..." }
    """
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

    data       = request.get_json(silent=True) or {}
    reason     = (data.get('reason') or '').strip() or None
    email      = user.email
    first_name = user.first_name

    db.session.delete(user)
    db.session.commit()

    logger.info(
        "Staff rejected: user_id=%d council_id=%d by actor_id=%d reason=%r",
        user_id, council_id, current_user.id, reason,
    )

    # Notify the applicant (best-effort)
    try:
        from app.common import email_service
        from app.common.email_service import send_email
        subject    = 'Your GrantThrive staff account request was not approved'
        body_lines = [
            f'<p>Hi {first_name},</p>',
            f'<p>Your request to join <strong>{council.name}</strong> on GrantThrive '
            'could not be approved at this time.</p>',
        ]
        if reason:
            body_lines.append(f'<p><strong>Reason:</strong> {reason}</p>')
        body_lines.append(
            '<p>If you believe this is an error, please contact your Council Administrator.</p>'
        )
        send_email(email, subject, ''.join(body_lines))
    except Exception as _ne:
        logger.warning("Staff rejection email failed for user_id=%d: %s", user_id, _ne)

    return jsonify({'message': 'Staff member rejected and notified.'}), 200


# ── SMS Settings ──────────────────────────────────────────────────────────────

@councils_bp.route('/councils/<int:council_id>/sms-settings', methods=['GET'])
@token_required
@role_required('council_admin', 'system_admin')
def get_sms_settings(current_user, council_id):
    """Return SMS settings and entitlement status for a council."""
    if current_user.role == 'council_admin' and current_user.council_id != council_id:
        return jsonify({'error': 'Access denied'}), 403

    council = Council.query.get_or_404(council_id)

    from app.common.plans import get_plan_limits, can_use_feature
    limits = get_plan_limits(council.plan)

    return jsonify({
        'sms_enabled':             council.addon_sms,
        'sms_included_in_plan':    limits.sms_included,
        'sms_addon_available':     limits.sms_addon_available,
        'can_use_sms':             can_use_feature(council, 'sms'),
        'sms_event_prefs':         council.sms_event_prefs or _default_sms_prefs(),
        'sms_business_hours_only': council.sms_business_hours_only,
        'sms_timezone':            council.sms_timezone or 'Australia/Sydney',
        'plan':                    council.plan,
    }), 200


@councils_bp.route('/councils/<int:council_id>/sms-settings', methods=['PATCH'])
@token_required
@role_required('council_admin', 'system_admin')
def update_sms_settings(current_user, council_id):
    """Update SMS notification preferences for a council."""
    if current_user.role == 'council_admin' and current_user.council_id != council_id:
        return jsonify({'error': 'Access denied'}), 403

    council = Council.query.get_or_404(council_id)

    from app.common.plans import can_use_feature
    if not can_use_feature(council, 'sms'):
        return jsonify({
            'error': 'SMS is not enabled for your plan. Please upgrade or contact GrantThrive support.'
        }), 403

    data = request.get_json(silent=True) or {}

    if 'sms_event_prefs' in data and isinstance(data['sms_event_prefs'], dict):
        council.sms_event_prefs = data['sms_event_prefs']

    if 'sms_business_hours_only' in data:
        council.sms_business_hours_only = bool(data['sms_business_hours_only'])

    if 'sms_timezone' in data and isinstance(data['sms_timezone'], str):
        council.sms_timezone = data['sms_timezone'][:60]

    db.session.commit()
    return jsonify({'message': 'SMS settings updated successfully.'}), 200


@councils_bp.route('/councils/<int:council_id>/sms-settings/test', methods=['POST'])
@token_required
@role_required('council_admin', 'system_admin')
def send_test_sms(current_user, council_id):
    """Send a test SMS to the council admin's registered phone number."""
    if current_user.role == 'council_admin' and current_user.council_id != council_id:
        return jsonify({'error': 'Access denied'}), 403

    council = Council.query.get_or_404(council_id)

    from app.common.plans import can_use_feature
    if not can_use_feature(council, 'sms'):
        return jsonify({'error': 'SMS is not enabled for your plan.'}), 403

    phone = getattr(current_user, 'phone', None)
    if not phone:
        return jsonify({
            'error': 'No phone number on your account. Please update your profile first.'
        }), 400

    from app.common.sms_service import send_sms
    ok, result = send_sms(
        to_phone=phone,
        body=f"GrantThrive test message for {council.name}. SMS notifications are working correctly.",
        council_id=council_id,
    )

    if ok:
        return jsonify({'message': 'Test SMS sent successfully.', 'sid': result}), 200
    return jsonify({'error': f'SMS send failed: {result}'}), 500


@councils_bp.route('/councils/<int:council_id>/sms-usage', methods=['GET'])
@token_required
@role_required('council_admin', 'system_admin')
def get_sms_usage(current_user, council_id):
    """Return SMS usage statistics for the council (last 30 days)."""
    if current_user.role == 'council_admin' and current_user.council_id != council_id:
        return jsonify({'error': 'Access denied'}), 403

    from datetime import date, timedelta
    from app.models import CouncilSmsUsage

    today = date.today()
    thirty_days_ago = today - timedelta(days=30)

    rows = CouncilSmsUsage.query.filter(
        CouncilSmsUsage.council_id == council_id,
        CouncilSmsUsage.date >= thirty_days_ago,
    ).order_by(CouncilSmsUsage.date.desc()).all()

    total = sum(r.messages_sent for r in rows)

    return jsonify({
        'total_last_30_days': total,
        'daily': [
            {'date': r.date.isoformat(), 'messages_sent': r.messages_sent}
            for r in rows
        ],
    }), 200


def _default_sms_prefs() -> dict:
    """Return the default SMS event preferences (all enabled)."""
    return {
        'application_received': True,
        'application_approved': True,
        'application_rejected': True,
        'deadline_reminder':    True,
        'document_required':    True,
        'payment_processed':    True,
        'voting_reminder':      True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SMS Add-on Tier Selection
# Councils self-select their SMS tier from Account & Billing or Communications
# Settings.  Selecting a tier sets addon_sms=True and records the chosen tier.
# Cancellation sets addon_sms=False and clears the tier.
# ─────────────────────────────────────────────────────────────────────────────

# Tier definitions — kept in sync with the pricing model document.
SMS_TIERS = {
    'starter': {
        'name':              'SMS Starter',
        'included_messages': 500,
        'price_aud_cents':   1900,   # $19/mo
        'overage_cents':     15,     # $0.15/msg
        'min_plan':          'small',
    },
    'growth': {
        'name':              'SMS Growth',
        'included_messages': 2000,
        'price_aud_cents':   6900,   # $69/mo
        'overage_cents':     15,
        'min_plan':          'small',
    },
    'professional': {
        'name':              'SMS Professional',
        'included_messages': 10000,
        'price_aud_cents':   19900,  # $199/mo
        'overage_cents':     12,
        'min_plan':          'small',  # available to all paid plans
    },
    'enterprise': {
        'name':              'SMS Enterprise',
        'included_messages': 50000,
        'price_aud_cents':   59900,  # $599/mo
        'overage_cents':     10,
        'min_plan':          'small',  # available to all paid plans
    },
}

# Plan hierarchy for eligibility checks
_PLAN_RANK = {'trial': 0, 'small': 1, 'medium': 2, 'large': 3}


def _plan_qualifies(council_plan: str, min_plan: str) -> bool:
    """Return True if council_plan meets or exceeds min_plan."""
    return _PLAN_RANK.get(council_plan, 0) >= _PLAN_RANK.get(min_plan, 99)


@councils_bp.route('/councils/<int:council_id>/sms-tiers', methods=['GET'])
@token_required
def get_sms_tiers(current_user, council_id):
    """Return available SMS tiers and the council's current selection."""
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    council_plan = council.plan or 'trial'

    tiers = []
    for key, t in SMS_TIERS.items():
        eligible = _plan_qualifies(council_plan, t['min_plan'])
        tiers.append({
            'key':               key,
            'name':              t['name'],
            'included_messages': t['included_messages'],
            'price_aud_cents':   t['price_aud_cents'],
            'overage_cents':     t['overage_cents'],
            'min_plan':          t['min_plan'],
            'eligible':          eligible,
        })

    return jsonify({
        'tiers':        tiers,
        'current_tier': council.sms_tier,
        'addon_sms':    council.addon_sms,
        'council_plan': council_plan,
    }), 200


@councils_bp.route('/councils/<int:council_id>/sms-tiers', methods=['POST'])
@token_required
def select_sms_tier(current_user, council_id):
    """Select or change the SMS add-on tier for a council.

    Body: { "tier": "starter" | "growth" | "professional" | "enterprise" }
    """
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    data = request.get_json(silent=True) or {}
    tier_key = data.get('tier', '').lower().strip()

    if tier_key not in SMS_TIERS:
        return jsonify({'error': f'Invalid tier. Choose from: {", ".join(SMS_TIERS)}'}), 400

    tier = SMS_TIERS[tier_key]
    council_plan = council.plan or 'trial'

    if not _plan_qualifies(council_plan, tier['min_plan']):
        return jsonify({
            'error': (
                f'The {tier["name"]} tier requires the '
                f'{tier["min_plan"].title()} Council plan or higher. '
                f'Your current plan is {council_plan.title()} Council.'
            )
        }), 403

    previous_tier = council.sms_tier
    council.sms_tier  = tier_key
    council.addon_sms = True
    db.session.commit()

    logger.info(
        "SMS tier selected: council_id=%d tier=%s (was %s) by user_id=%d",
        council_id, tier_key, previous_tier, current_user.id,
    )

    return jsonify({
        'message':      f'SMS {tier["name"]} add-on activated successfully.',
        'tier':         tier_key,
        'tier_details': tier,
        'addon_sms':    True,
    }), 200


@councils_bp.route('/councils/<int:council_id>/sms-tiers', methods=['DELETE'])
@token_required
def cancel_sms_tier(current_user, council_id):
    """Cancel the SMS add-on for a council."""
    council = db.session.get(Council, council_id)
    if not council:
        return jsonify({'error': 'Council not found.'}), 404

    is_system_admin = current_user.role == 'system_admin'
    is_own_admin    = (current_user.role == 'council_admin' and
                       current_user.council_id == council_id)
    if not is_system_admin and not is_own_admin:
        return jsonify({'error': 'Access denied.'}), 403

    previous_tier     = council.sms_tier
    council.sms_tier  = None
    council.addon_sms = False
    db.session.commit()

    logger.info(
        "SMS tier cancelled: council_id=%d (was %s) by user_id=%d",
        council_id, previous_tier, current_user.id,
    )

    return jsonify({'message': 'SMS add-on cancelled successfully.'}), 200
