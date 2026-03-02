"""
GrantThrive — Authentication Decorators
========================================
JWT-based route protection decorators for use across all blueprints.

All authentication in GrantThrive is JWT-based.  These decorators read the
``Authorization: Bearer <token>`` header, validate the token, and inject the
authenticated ``User`` object as the first argument to the decorated function.

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
from datetime import datetime, timezone

from flask import request, jsonify, current_app

from app.models import User
from app import db

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

JWT_ALGORITHM = "HS256"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _decode_token(token: str) -> dict:
    """Decode and validate a JWT. Returns the payload dict or raises."""
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[JWT_ALGORITHM],
    )


def _get_bearer_token() -> str | None:
    """Extract the Bearer token from the Authorization header, or None."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]
    return None


# ── Public decorators ─────────────────────────────────────────────────────────

def token_required(f):
    """
    Decorator: require a valid JWT in the Authorization header.

    Injects the authenticated ``User`` object as the first positional argument
    to the decorated view function.

    Returns 401 if the token is missing, expired, or invalid.
    Returns 401 if the associated user account does not exist or is inactive.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _get_bearer_token()
        if not token:
            return jsonify({"error": "Authentication required."}), 401

        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        user = db.session.get(User, int(payload["sub"]))
        if not user or not user.is_active:
            return jsonify({"error": "User account not found or inactive."}), 401

        return f(user, *args, **kwargs)

    return decorated


def role_required(*roles):
    """
    Decorator: require the authenticated user to have one of the given roles.

    Must be applied *after* ``@token_required`` (i.e. listed *before* it in
    the decorator stack, since decorators are applied bottom-up).

    Example:
        @bp.route('/admin')
        @role_required('council_admin', 'system_admin')
        def admin_view(current_user):
            ...

    Returns 403 if the user's role is not in the allowed list.
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                logger.warning(
                    "Access denied: user_id=%d role=%s required=%s",
                    current_user.id, current_user.role, roles,
                )
                return jsonify({"error": "Insufficient permissions."}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator
