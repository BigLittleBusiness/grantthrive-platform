"""
GrantThrive — RBAC Permission System
======================================
Centralised role-based access control for all API endpoints.

Roles (in ascending privilege order):
  community_member        — Public registered users; can browse grants and apply
  professional_consultant — External grant writers; can manage their own applications
  council_staff           — Council employees; can review applications and manage workflows
  council_admin           — Council administrators; full control over their council's data
  system_admin            — GrantThrive staff; cross-tenant superuser access

Permission strings follow the pattern:  <resource>:<action>
  e.g.  grants:read, applications:approve, councils:create

Tenant scoping:
  All council-scoped roles (council_admin, council_staff, community_member,
  professional_consultant) are additionally scoped to their council_id at the
  decorator level.  system_admin bypasses all tenant checks.

Usage:
    from app.common.permissions import permission_required, own_council_required

    @bp.route('/grants', methods=['POST'])
    @permission_required('grants:create')
    def create_grant(current_user):
        ...

    @bp.route('/councils/<int:council_id>/users')
    @own_council_required('users:read')
    def list_council_users(current_user, council_id):
        ...
"""

import logging
from functools import wraps

from flask import request, jsonify, current_app
import jwt

from app import db
from app.models import User

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"

# ── Permission Matrix ─────────────────────────────────────────────────────────
#
# Maps each role to the set of permissions it holds.
# system_admin implicitly holds ALL permissions — checked separately.

ROLE_PERMISSIONS: dict[str, set[str]] = {

    "community_member": {
        # Grants
        "grants:read",
        "grants:list",
        # Applications — own only (enforced in view logic)
        "applications:create",
        "applications:read_own",
        "applications:update_own",
        "applications:delete_own",
        # Voting
        "voting:cast",
        "voting:read",
        # Profile
        "profile:read",
        "profile:update",
        # Resources
        "resources:read",
    },

    "professional_consultant": {
        # Grants
        "grants:read",
        "grants:list",
        # Applications — own only (enforced in view logic)
        "applications:create",
        "applications:read_own",
        "applications:update_own",
        "applications:delete_own",
        # Voting
        "voting:read",
        # Profile
        "profile:read",
        "profile:update",
        # Resources
        "resources:read",
        # Consultant-specific
        "consultant:manage_clients",
        "consultant:read_reports",
    },

    "council_staff": {
        # Grants — read only; creation is admin-only
        "grants:read",
        "grants:list",
        # Applications — can read all within council; can review
        "applications:read",
        "applications:review",
        "applications:update_status",
        # Workflows
        "workflows:read",
        "workflows:update",
        # Voting
        "voting:read",
        "voting:manage",
        # Mapping
        "mapping:read",
        # Reports — read only
        "reports:read",
        # Profile
        "profile:read",
        "profile:update",
        # Resources
        "resources:read",
    },

    "council_admin": {
        # Grants — full CRUD within own council
        "grants:read",
        "grants:list",
        "grants:create",
        "grants:update",
        "grants:delete",
        "grants:publish",
        # Applications — full access within council
        "applications:read",
        "applications:review",
        "applications:approve",
        "applications:reject",
        "applications:update_status",
        "applications:delete",
        # Workflows — full CRUD
        "workflows:read",
        "workflows:create",
        "workflows:update",
        "workflows:delete",
        # Voting — full management
        "voting:read",
        "voting:manage",
        "voting:create",
        "voting:delete",
        # Mapping
        "mapping:read",
        "mapping:update",
        # Reports — full access
        "reports:read",
        "reports:export",
        "reports:financial",
        # Users — manage within own council
        "users:read",
        "users:create",
        "users:update",
        "users:deactivate",
        # Council profile
        "council:read",
        "council:update",
        # QR codes
        "qr:manage",
        # Communications
        "communications:manage",
        # Profile
        "profile:read",
        "profile:update",
        # Resources
        "resources:read",
        "resources:manage",
    },
}

# system_admin gets everything — represented as a sentinel
SYSTEM_ADMIN_ROLE = "system_admin"

ALL_PERMISSIONS: set[str] = set().union(*ROLE_PERMISSIONS.values()) | {
    # system_admin-only permissions
    "councils:create",
    "councils:list",
    "councils:delete",
    "system_admins:create",
    "system_admins:read",
    "system_admins:update",
    "system_admins:delete",
    "platform:analytics",
    "platform:billing",
    "platform:security",
    "platform:settings",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_bearer_token() -> str | None:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


def _resolve_user_from_token() -> tuple[User | None, str | None]:
    """
    Decode the JWT and return (user, error_message).
    Returns (None, error) on any failure.
    """
    token = _get_bearer_token()
    if not token:
        return None, "Authentication required."

    try:
        payload = jwt.decode(
            token,
            current_app.config["SECRET_KEY"],
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        return None, "Token has expired. Please log in again."
    except jwt.InvalidTokenError:
        return None, "Invalid token."

    user = db.session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        return None, "User account not found or inactive."

    return user, None


def has_permission(user: User, permission: str) -> bool:
    """Return True if the user holds the given permission."""
    if user.role == SYSTEM_ADMIN_ROLE:
        return True
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def get_user_permissions(user: User) -> set[str]:
    """Return the full set of permissions for a user."""
    if user.role == SYSTEM_ADMIN_ROLE:
        return ALL_PERMISSIONS
    return ROLE_PERMISSIONS.get(user.role, set())


# ── Decorators ────────────────────────────────────────────────────────────────

def permission_required(permission: str):
    """
    Decorator: require a valid JWT and a specific permission.

    Injects the authenticated User as the first argument to the view.

    Returns 401 if unauthenticated.
    Returns 403 if the user lacks the required permission.

    Example:
        @bp.route('/grants', methods=['POST'])
        @permission_required('grants:create')
        def create_grant(current_user):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user, error = _resolve_user_from_token()
            if error:
                return jsonify({"error": error}), 401

            if not has_permission(user, permission):
                logger.warning(
                    "Permission denied: user_id=%d role=%s required=%s",
                    user.id, user.role, permission,
                )
                return jsonify({"error": "Insufficient permissions.", "required": permission}), 403

            return f(user, *args, **kwargs)
        return decorated
    return decorator


def own_council_required(permission: str):
    """
    Decorator: require a valid JWT, a specific permission, AND that the
    authenticated user belongs to the council referenced in the URL.

    Expects the URL to contain a ``council_id`` parameter.
    system_admin bypasses the council ownership check.

    Example:
        @bp.route('/councils/<int:council_id>/users')
        @own_council_required('users:read')
        def list_council_users(current_user, council_id):
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user, error = _resolve_user_from_token()
            if error:
                return jsonify({"error": error}), 401

            if not has_permission(user, permission):
                logger.warning(
                    "Permission denied: user_id=%d role=%s required=%s",
                    user.id, user.role, permission,
                )
                return jsonify({"error": "Insufficient permissions.", "required": permission}), 403

            # Tenant scope check (system_admin is exempt)
            if user.role != SYSTEM_ADMIN_ROLE:
                council_id = kwargs.get("council_id")
                if council_id and user.council_id != council_id:
                    logger.warning(
                        "Cross-tenant access attempt: user_id=%d council_id=%s "
                        "tried to access council_id=%s",
                        user.id, user.council_id, council_id,
                    )
                    return jsonify({"error": "Access restricted to your own council."}), 403

            return f(user, *args, **kwargs)
        return decorated
    return decorator


def same_council_or_system_admin(f):
    """
    Decorator: require a valid JWT and that the user either belongs to the
    council referenced in the URL, or is a system_admin.

    No specific permission check — use when any authenticated council member
    should have access (e.g. reading their own council profile).
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user, error = _resolve_user_from_token()
        if error:
            return jsonify({"error": error}), 401

        if user.role != SYSTEM_ADMIN_ROLE:
            council_id = kwargs.get("council_id")
            if council_id and user.council_id != council_id:
                return jsonify({"error": "Access restricted to your own council."}), 403

        return f(user, *args, **kwargs)
    return decorated
