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
from werkzeug.security import generate_password_hash

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

    council = Council(
        name             = name,
        subdomain        = subdomain,
        slug             = slug,
        state            = state,
        lga_code         = (data.get('lga_code') or '').strip() or None,
        plan             = data.get('plan', 'starter'),
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
            password_hash = generate_password_hash(admin_pass),
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
        'message': f'Council "{name}" provisioned successfully.',
        'council': council.to_dict(),
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
        password_hash = generate_password_hash(password),
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
