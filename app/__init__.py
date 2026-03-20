"""
GrantThrive — Application Factory
=================================
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
omitted until those features are built. They will be added here when ready.
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
                "FATAL: SECRET_KEY has not been set. "
                "Set a strong random SECRET_KEY environment variable before "
                "starting the application in production."
            )

    # ── Extensions ──────────────────────────────────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ── CORS ────────────────────────────────────────────────────────────────
    # All UI apps are served from subdomains of granthrive.com and share
    # JWT-based auth. Council tenant portals are served from
    # <tenant>.granthrive.com — the regex covers all of them.
    #
    # supports_credentials=True means:
    # - do NOT use "*"
    # - browser must see an explicit allowed origin
    #
    # Note:
    # - regex origins work with Flask-CORS
    # - include localhost ports used by Vite / React dev servers
    allowed_origins = app.config.get(
        "CORS_ORIGINS",
        [
            # Production root / fixed apps
            "https://granthrive.com",
            "https://www.granthrive.com",
            "https://app.granthrive.com",
            "https://admin.granthrive.com",
            "https://map.granthrive.com",
            "https://roi.granthrive.com",

            # Tenant portals
            r"https://.*\.granthrive\.com",

            # Local development
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:4173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:4173",
            "http://127.0.0.1:5173",
        ],
    )

    CORS(
        app,
        resources={
            r"/auth/*": {"origins": allowed_origins},
            r"/api/*": {"origins": allowed_origins},
            r"/public/*": {"origins": allowed_origins},
            r"/reports/*": {"origins": allowed_origins},
            r"/workflows/*": {"origins": allowed_origins},
            r"/voting/*": {"origins": allowed_origins},
            r"/mapping/*": {"origins": allowed_origins},
            r"/*": {"origins": allowed_origins},  # fallback
        },
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "Accept",
            "Origin",
        ],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        expose_headers=["Content-Disposition"],
    )

    # ── Optional performance optimizations ─────────────────────────────────
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

    # ── Flask-Login configuration ───────────────────────────────────────────
    # The login_view is only used for server-rendered redirects (legacy).
    # All React apps use the JWT-based /auth/login endpoint instead.
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"

    # ── Blueprint registration ──────────────────────────────────────────────

    # Core authentication (JWT-based SSO)
    # Mounted at both /auth (legacy server-rendered) and /api/auth (React frontend)
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_api")

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

    # System Admin: GrantThrive staff management
    # (add/edit/deactivate system_admin users)
    from app.system_admin import bp as system_admin_bp
    app.register_blueprint(system_admin_bp, url_prefix="/api")

    # Pricing: live pricing configuration management
    from app.pricing import pricing_bp
    app.register_blueprint(pricing_bp)

    # Forum: community discussion forums
    from app.forum import forum_bp
    app.register_blueprint(forum_bp, url_prefix="/api")

    # Notifications: in-app notification bell API
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp)

    # ── Tenant resolution middleware ────────────────────────────────────────
    # Runs before every request to resolve the council tenant from subdomain.
    from app.tenancy.middleware import resolve_tenant

    @app.before_request
    def resolve_tenant_safe():
        # Let CORS preflight pass cleanly
        from flask import request
        if request.method == "OPTIONS":
            return None
        return resolve_tenant()

    # ── Template filters ────────────────────────────────────────────────────
    from app.common.formatters import register_template_filters
    register_template_filters(app)

    # ── Background scheduler (timed notification nudges) ───────────────────
    import os
    # Only start in the main process (not the Werkzeug reloader child)
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") != "false":
        from app.common.scheduled_jobs import init_scheduler
        init_scheduler(app)

    # ── Optional debug endpoint: useful while testing CORS locally ──────────
    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "service": "GrantThrive API"}, 200

    return app


# ── Flask-Login user loader ───────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id: str):
    """Load a user by their primary key for Flask-Login session management."""
    from app.models import User
    return db.session.get(User, int(user_id))