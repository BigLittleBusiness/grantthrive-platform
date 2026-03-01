"""
GrantThrive — Authentication Routes
=====================================
Provides JWT-based authentication endpoints consumed by all GrantThrive UI apps
via the shared @grantthrive/auth library.

Endpoints:
  POST /auth/login          — Email + password login; returns JWT + user profile
  POST /auth/logout         — Invalidate token (client-side; server logs the event)
  POST /auth/register       — New user registration (requires admin approval)
  POST /auth/verify-token   — Validate a JWT and return the current user profile
  POST /auth/demo-login     — Demo login for development/testing environments
  POST /auth/change-password — Change authenticated user's password

Domain: grantthrive.com
"""

import jwt
import logging
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import request, jsonify, current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app import db
from app.auth import bp
from app.models import User

logger = logging.getLogger(__name__)

# ── JWT helpers ───────────────────────────────────────────────────────────────

JWT_ALGORITHM  = "HS256"
JWT_EXPIRY_DAYS = 7


def _generate_token(user):
    """Issue a signed JWT for the given user."""
    payload = {
        "sub":   str(user.id),
        "email": user.email,
        "role":  user.role,
        "iat":   datetime.now(timezone.utc),
        "exp":   datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm=JWT_ALGORITHM)


def _decode_token(token):
    """Decode and validate a JWT. Returns the payload dict or raises."""
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=[JWT_ALGORITHM])


def _user_to_dict(user):
    """Serialise a User record to a safe dict for API responses."""
    return {
        "id":         user.id,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "full_name":  f"{user.first_name} {user.last_name}",
        "role":       user.role,
        "is_active":  user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }


def token_required(f):
    """Decorator: require a valid JWT in the Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authentication required."}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired. Please log in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        user = User.query.get(int(payload["sub"]))
        if not user or not user.is_active:
            return jsonify({"error": "User account not found or inactive."}), 401

        return f(user, *args, **kwargs)
    return decorated


def role_required(*roles):
    """Decorator: require the authenticated user to have one of the given roles."""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator


# ── Routes ────────────────────────────────────────────────────────────────────

@bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user with email and password.

    Request body:
        { "email": "...", "password": "..." }

    Response (200):
        { "token": "<jwt>", "user": { ... } }
    """
    data = request.get_json(silent=True) or {}
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        logger.warning("Failed login attempt for email: %s", email)
        return jsonify({"error": "Invalid email or password."}), 401

    if not user.is_active:
        return jsonify({"error": "Your account is pending approval or has been suspended."}), 403

    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.session.commit()

    token = _generate_token(user)
    logger.info("Successful login: user_id=%d role=%s", user.id, user.role)

    return jsonify({
        "token": token,
        "user":  _user_to_dict(user),
    }), 200


@bp.route("/logout", methods=["POST"])
def logout():
    """
    Log out the current user.

    JWTs are stateless — the client is responsible for discarding the token.
    This endpoint exists so the server can log the event and, in future,
    maintain a token denylist if required.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload = _decode_token(token)
            logger.info("Logout: user_id=%s", payload.get("sub"))
        except jwt.InvalidTokenError:
            pass  # Token already invalid — that is fine
    return jsonify({"message": "Logged out successfully."}), 200


@bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.

    New accounts are created with is_active=False and require admin approval
    before the user can log in.

    Request body:
        {
          "email": "...", "password": "...",
          "first_name": "...", "last_name": "...",
          "role": "community_member"   (optional, default: community_member)
        }
    """
    data = request.get_json(silent=True) or {}
    email      = (data.get("email") or "").strip().lower()
    password   = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name  = (data.get("last_name") or "").strip()
    role       = data.get("role", "community_member")

    # Validate required fields
    if not all([email, password, first_name, last_name]):
        return jsonify({"error": "Email, password, first name, and last name are required."}), 400

    # Only allow safe self-registration roles
    allowed_roles = {"community_member", "professional_consultant"}
    if role not in allowed_roles:
        role = "community_member"

    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists."}), 409

    # Generate a unique username from email
    base_username = email.split("@")[0]
    username = base_username
    counter  = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{counter}"
        counter += 1

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
        is_active=False,  # Requires admin approval
    )
    db.session.add(user)
    db.session.commit()

    logger.info("New registration: user_id=%d email=%s role=%s (pending approval)", user.id, email, role)

    return jsonify({
        "message": "Registration successful. Your account is pending approval.",
        "user": _user_to_dict(user),
        "requires_approval": True,
    }), 201


@bp.route("/verify-token", methods=["POST"])
def verify_token():
    """
    Validate a JWT and return the current user profile.

    Used by all GrantThrive apps on load to confirm the stored token is still
    valid and to refresh the user profile (e.g. if role changed).

    Request body:
        { "token": "<jwt>" }

    Response (200):
        { "valid": true, "user": { ... } }

    Response (401):
        { "valid": false, "error": "..." }
    """
    data  = request.get_json(silent=True) or {}
    token = data.get("token") or ""

    # Also accept token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if not token and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]

    if not token:
        return jsonify({"valid": False, "error": "No token provided."}), 401

    try:
        payload = _decode_token(token)
    except jwt.ExpiredSignatureError:
        return jsonify({"valid": False, "error": "Token has expired."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"valid": False, "error": "Invalid token."}), 401

    user = User.query.get(int(payload["sub"]))
    if not user or not user.is_active:
        return jsonify({"valid": False, "error": "User not found or inactive."}), 401

    return jsonify({
        "valid": True,
        "user":  _user_to_dict(user),
    }), 200


@bp.route("/demo-login", methods=["POST"])
def demo_login():
    """
    Demo login for development and testing environments.

    Only available when FLASK_ENV != 'production'.

    Request body:
        { "demo_type": "council_admin" | "council_staff" | "community_member" |
                       "professional_consultant" | "system_admin" }
    """
    if current_app.config.get("ENV") == "production" or \
       not current_app.config.get("TESTING") and \
       current_app.config.get("FLASK_ENV") == "production":
        return jsonify({"error": "Demo login is not available in production."}), 403

    data      = request.get_json(silent=True) or {}
    demo_type = data.get("demo_type", "council_admin")

    demo_users = {
        "council_admin": {
            "email": "demo.admin@melbourne.vic.gov.au",
            "first_name": "Demo",
            "last_name": "Council Admin",
            "role": "council_admin",
        },
        "council_staff": {
            "email": "demo.staff@melbourne.vic.gov.au",
            "first_name": "Demo",
            "last_name": "Council Staff",
            "role": "council_staff",
        },
        "community_member": {
            "email": "demo.community@example.com",
            "first_name": "Demo",
            "last_name": "Community Member",
            "role": "community_member",
        },
        "professional_consultant": {
            "email": "demo.consultant@grantsuccess.com",
            "first_name": "Demo",
            "last_name": "Consultant",
            "role": "professional_consultant",
        },
        "system_admin": {
            "email": "demo.sysadmin@grantthrive.com",
            "first_name": "Demo",
            "last_name": "System Admin",
            "role": "system_admin",
        },
    }

    profile = demo_users.get(demo_type, demo_users["council_admin"])

    # Find or create the demo user
    user = User.query.filter_by(email=profile["email"]).first()
    if not user:
        base_username = profile["email"].split("@")[0].replace(".", "_")
        user = User(
            username=base_username,
            email=profile["email"],
            password_hash=generate_password_hash("demo_password_not_for_production"),
            first_name=profile["first_name"],
            last_name=profile["last_name"],
            role=profile["role"],
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

    user.last_login = datetime.utcnow()
    db.session.commit()

    token = _generate_token(user)
    return jsonify({
        "token": token,
        "user":  _user_to_dict(user),
    }), 200


@bp.route("/change-password", methods=["POST"])
@token_required
def change_password(current_user):
    """
    Change the authenticated user's password.

    Request body:
        { "current_password": "...", "new_password": "..." }
    """
    data             = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password     = data.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "Current and new passwords are required."}), 400

    if len(new_password) < 8:
        return jsonify({"error": "New password must be at least 8 characters."}), 400

    if not check_password_hash(current_user.password_hash, current_password):
        return jsonify({"error": "Current password is incorrect."}), 401

    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()

    logger.info("Password changed: user_id=%d", current_user.id)
    return jsonify({"message": "Password changed successfully."}), 200
