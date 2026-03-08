"""
GrantThrive — Application Factory
====================================
Creates and configures the Flask application instance.

Blueprint layout:
  /auth/*        — JWT authentication (login, register, verify-token, etc.)
  /              — Main routes (homepage, dashboard, public grant listing)
  /reports/*     — Report generation and download
  /workflows/*   — Grant workflow management (pending approvals, etc.)
  /voting/*      — Community voting on grant applications
  /mapping/*     — Interactive grant geographic mapping
  /public/*      — Public transparency dashboard and API
  /api/health    — Health-check endpoint for CI/CD and load-balancer probes

Blueprints for grants, applications, reviews, and admin are intentionally
omitted until those features are built.  They will be added here when ready.
  /api/system-admins — System admin user management (GrantThrive staff CRUD)
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.config import Config

# ── Extension singletons ──────────────────────────────────────────────────────
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],          # No global limit — apply per-route only
    storage_uri="memory://",    # Use Redis URI in production: "redis://..."
)


def create_app(config_class=Config):
    """Create and configure the Flask application.

    Args:
        config_class: A configuration class from ``config.config``.
                      Defaults to :class:`config.config.Config`.

    Returns:
        A fully configured :class:`flask.Flask` application instance.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Security check: refuse to start in production with default secret ──
    if (
        app.config.get("ENV") == "production"
        or app.config.get("FLASK_ENV") == "production"
    ):
        if app.config.get("SECRET_KEY") == "change-me-in-production":
            raise RuntimeError(
                "FATAL: SECRET_KEY has not been set.  "
                "Set a strong random SECRET_KEY environment variable before "
                "starting the application in production."
            )
    # ── Extensions ──────────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)
    # ── CORS ──────────────────────────────────────────────────────────────────
    # All five UI apps are served from subdomains of grantthrive.com and share
    # the same JWT-based SSO session.  Council tenant portals are served from
    # <subdomain>.grantthrive.com — the wildcard pattern covers all of them.
    # In development, localhost ports are also permitted.
    # The wildcard origin ("*") is intentionally NOT used so that
    # supports_credentials=True works correctly (browsers reject wildcard +
    # credentials).
    allowed_origins = app.config.get("CORS_ORIGINS", [
        # Production — fixed subdomains
        "https://grantthrive.com",
        "https://app.grantthrive.com",
        "https://admin.grantthrive.com",
        "https://map.grantthrive.com",
        "https://roi.grantthrive.com",
        # Production — council tenant portals (wildcard pattern)
        r"https://.*\.grantthrive\.com",
        # Local development (Vite default ports)
        "http://localhost:5173"
    ])
    CORS(app, origins=allowed_origins, supports_credentials=True)
    # ── Optional performance optimizations ────────────────────────────────────
    try:
        from app.optimizations import (
            init_optimizations,
            PerformanceMiddleware,
            optimize_db_connection,
        )
        init_optimizations(app)
        PerformanceMiddleware(app)
        optimize_db_connection(app)
    except ImportError:
        pass  # Optimizations module not available — safe to skip

    # ── Flask-Login configuration ─────────────────────────────────────────────
    # The login_view is only used for server-rendered redirects (legacy).
    # All React apps use the JWT-based /auth/login endpoint instead.
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # ── Blueprint registration ────────────────────────────────────────────────

    # Core authentication (JWT-based SSO)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    # Main routes: homepage, dashboard, public grant listing
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Reports: PDF generation and download
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix="/reports")

    # Workflows: pending approvals, grant processing pipeline
    from app.workflows import bp as workflows_bp
    app.register_blueprint(workflows_bp, url_prefix="/workflows")

    # Voting: community voting on grant applications
    from app.voting import voting as voting_bp
    app.register_blueprint(voting_bp, url_prefix="/voting")

    # Mapping: interactive geographic grant map
    from app.mapping import mapping as mapping_bp
    app.register_blueprint(mapping_bp, url_prefix="/mapping")

    # Public: transparency dashboard and public data API
    from app.public import public as public_bp
    app.register_blueprint(public_bp, url_prefix="/public")

    # API: health-check endpoint
    from app.api.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api")

    # Tenancy: council provisioning and management API
    from app.tenancy.routes import councils_bp
    app.register_blueprint(councils_bp, url_prefix="/api")

    # System Admin: GrantThrive staff management (add/edit/deactivate system_admin users)
    from app.system_admin import bp as system_admin_bp
    app.register_blueprint(system_admin_bp, url_prefix="/api")

    # Pricing: live pricing configuration management
    from app.pricing import pricing_bp
    app.register_blueprint(pricing_bp)

    # Forum: community discussion forums (council staff ↔ community)
    from app.forum import forum_bp
    app.register_blueprint(forum_bp, url_prefix='/api')

    # ── Tenant resolution middleware ──────────────────────────────────────────
    # Runs before every request to resolve the council tenant from the subdomain.
    from app.tenancy.middleware import resolve_tenant
    app.before_request(resolve_tenant)

    # ── Template filters ──────────────────────────────────────────────────────
    from app.common.formatters import register_template_filters
    register_template_filters(app)

    return app


# ── Flask-Login user loader ───────────────────────────────────────────────────

@login_manager.user_loader
def load_user(user_id: str):
    """Load a user by their primary key for Flask-Login session management."""
    from app.models import User
    return db.session.get(User, int(user_id))
