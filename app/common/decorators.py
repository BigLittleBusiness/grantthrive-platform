"""
GrantThrive — Authentication Decorators
========================================
JWT-based route protection decorators for use across all blueprints.

All authentication in GrantThrive is JWT-based. These decorators read the
`Authorization: Bearer <token>` header, validate the token, and inject the
authenticated `User` object as the first argument to the decorated function.

Usage:
    from app.common.decorators import token_required, role_required

    @bp.route('/my-route')
    @token_required
    def my_view(current_user):
        ...

    @bp.route('/admin-only')
    @role_required('council_admin', 'system_admin')
    def admin_view(current_user):
        ...
"""

import jwt
import logging
from functools import wraps

from flask import request, jsonify, current_app

from app.models import User
from app import db

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _decode_token(token: str) -> dict:
    """Decode and validate a JWT. Returns the payload dict or raises."""
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
    )


def _get_bearer_token():
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None


def _get_current_user_from_token():
    """
    Validates JWT and returns:
        (user, None) on success
        (None, (json_response, status_code)) on failure
    """
    token = _get_bearer_token()
    if not token:
        return None, (jsonify({"error": "Authentication required."}), 401)

    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return None, (jsonify({"error": "Token has expired. Please log in again."}), 401)
    except jwt.InvalidTokenError:
        return None, (jsonify({"error": "Invalid token."}), 401)

    user_id = payload.get("sub")
    if not user_id:
        return None, (jsonify({"error": "Invalid token payload."}), 401)

    try:
        user = db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None, (jsonify({"error": "Invalid token subject."}), 401)

    if not user or not getattr(user, "is_active", False):
        return None, (jsonify({"error": "User account not found or inactive."}), 401)

    return user, None


# ── Public decorators ─────────────────────────────────────────────────────────

def token_required(f):
    """
    Require a valid JWT in the Authorization header.

    Injects authenticated `User` as the first positional argument.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user, error = _get_current_user_from_token()
        if error:
            return error
        return f(current_user, *args, **kwargs)

    return decorated


def login_required_api(f):
    """
    Backward-compatible API auth decorator.

    Older modules may still import `login_required_api`.
    Functionally identical to `token_required`.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        current_user, error = _get_current_user_from_token()
        if error:
            return error
        return f(current_user, *args, **kwargs)

    return decorated


def role_required(*roles):
    """
    Require authenticated user to have one of the allowed roles.

    Example:
        @bp.route('/admin')
        @role_required('council_admin', 'system_admin')
        def admin_view(current_user):
            ...
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                logger.warning(
                    "Access denied: user_id=%s role=%s required=%s",
                    current_user.id,
                    current_user.role,
                    roles,
                )
                return jsonify({"error": "Insufficient permissions."}), 403

            return f(current_user, *args, **kwargs)

        return decorated

    return decorator