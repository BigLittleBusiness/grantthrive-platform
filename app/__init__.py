"""
GrantThrive — Application Factory

Every HTTP endpoint is served under /api. In production a reverse proxy (or
the host serving the built frontend) routes /api/* here and everything else
to the frontend.
"""

import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.config import Config

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

# Use Redis as the rate-limiter storage backend in production.
# Falls back to in-memory storage when REDIS_URL is not set (local dev / CI).
_REDIS_URL = os.environ.get("REDIS_URL")

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri=_REDIS_URL if _REDIS_URL else "memory://",
)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # ── Extensions ─────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    limiter.init_app(app)

    # ── CORS ───────────────────────────────────
    # Only needed when the frontend is served from a different origin than
    # the API. CORS_ORIGINS is a comma-separated list in .env.
    _cors_env = os.environ.get("CORS_ORIGINS", "")
    allowed_origins = [
        o.strip() for o in _cors_env.split(",") if o.strip()
    ] or [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://grantthrive.com",
        "https://www.grantthrive.com",
        "https://app.grantthrive.com",
        "https://admin.grantthrive.com",
        "https://map.grantthrive.com",
        "https://roi.grantthrive.com",
    ]

    CORS(
        app,
        resources={r"/api/*": {"origins": allowed_origins}},
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

    # ── Blueprints ─────────────────────────────
    from app.api.health import health_bp
    from app.auth import bp as auth_bp
    from app.tenancy.routes import councils_bp
    from app.tenancy import logo  # noqa: F401 — registers POST /api/councils/<id>/logo
    from app.system_admin import bp as system_admin_bp
    from app.grants import bp as grants_bp
    from app.applications import bp as applications_bp
    from app.notifications import bp as notifications_bp
    from app.forum import forum_bp
    from app.voting import voting as voting_bp
    from app.public import public as public_bp
    from app.mapping import mapping as mapping_bp
    from app.pricing.routes import pricing_bp
    from app.api.abn import abn_bp
    from app.contact import bp as contact_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(councils_bp, url_prefix="/api")
    app.register_blueprint(system_admin_bp, url_prefix="/api")
    app.register_blueprint(grants_bp, url_prefix="/api/grants")
    app.register_blueprint(applications_bp, url_prefix="/api/applications")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")
    app.register_blueprint(forum_bp, url_prefix="/api")
    app.register_blueprint(voting_bp, url_prefix="/api/voting")
    app.register_blueprint(public_bp, url_prefix="/api/public")
    app.register_blueprint(mapping_bp, url_prefix="/api/mapping")
    app.register_blueprint(pricing_bp, url_prefix="/api/pricing")
    app.register_blueprint(abn_bp, url_prefix="/api")
    app.register_blueprint(contact_bp, url_prefix="/api")

    # ── Tenant middleware ──────────────────────
    from app.tenancy.middleware import resolve_tenant

    @app.before_request
    def resolve_tenant_safe():
        if request.method == "OPTIONS":
            return None
        return resolve_tenant()

    # ── Scheduler ──────────────────────────────
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") != "false":
        from app.common.scheduled_jobs import init_scheduler
        init_scheduler(app)

    return app
