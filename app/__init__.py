"""
GrantThrive — Application Factory
"""

import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from config.config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
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
    login_manager.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # ── Performance / Caching ──────────────────
    from app.optimizations import init_optimizations
    init_optimizations(app)

    # ── CORS ───────────────────────────────────
    allowed_origins = {
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }

    frontend_base_url = os.environ.get("FRONTEND_BASE_URL")
    if frontend_base_url:
        allowed_origins.add(frontend_base_url.rstrip("/"))

    allowed_origins = sorted(allowed_origins)

    CORS(
        app,
        origins=allowed_origins,
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
        resources={
            r"/api/*": {"origins": allowed_origins},
            r"/auth/*": {"origins": allowed_origins},
            r"/public/*": {"origins": allowed_origins},
            r"/reports/*": {"origins": allowed_origins},
            r"/workflows/*": {"origins": allowed_origins},
            r"/voting/*": {"origins": allowed_origins},
            r"/mapping/*": {"origins": allowed_origins},
            r"/*": {"origins": allowed_origins},
        },
    )

    # ── Blueprints ─────────────────────────────

    # AUTH
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(auth_bp, url_prefix="/api/auth", name="auth_api")

    # MAIN
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # HEALTH
    from app.api.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/api")

    # TENANCY
    from app.tenancy.routes import councils_bp
    app.register_blueprint(councils_bp, url_prefix="/api")

    # SYSTEM ADMIN
    from app.system_admin import bp as system_admin_bp
    app.register_blueprint(system_admin_bp, url_prefix="/api")

    # REPORTS
    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix="/reports")

    # WORKFLOWS
    from app.workflows import bp as workflows_bp
    app.register_blueprint(workflows_bp, url_prefix="/workflows")

    # VOTING
    from app.voting import voting as voting_bp
    app.register_blueprint(voting_bp, url_prefix="/voting")

    # MAPPING
    from app.mapping import mapping as mapping_bp
    app.register_blueprint(mapping_bp, url_prefix="/mapping")

    # PUBLIC
    from app.public import public as public_bp
    app.register_blueprint(public_bp, url_prefix="/public")

    # FORUM
    from app.forum import forum_bp
    app.register_blueprint(forum_bp, url_prefix="/api")

    # NOTIFICATIONS
    from app.notifications import bp as notifications_bp
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")

    # APPLICATIONS API
    from app.applications import bp as applications_bp
    app.register_blueprint(applications_bp, url_prefix="/api/applications")

    # GRANTS API
    from app.grants import bp as grants_bp
    app.register_blueprint(grants_bp, url_prefix="/api/grants")

    # ABN VALIDATION (Australian Business Register)
    from app.api.abn import abn_bp
    app.register_blueprint(abn_bp, url_prefix="/api")

    # ── Tenant middleware ──────────────────────
    from app.tenancy.middleware import resolve_tenant

    @app.before_request
    def resolve_tenant_safe():
        if request.method == "OPTIONS":
            return None
        return resolve_tenant()

    # ── Template filters ───────────────────────
    from app.common.formatters import register_template_filters
    register_template_filters(app)

    # ── Scheduler ──────────────────────────────
    if not app.testing and os.environ.get("WERKZEUG_RUN_MAIN") != "false":
        from app.common.scheduled_jobs import init_scheduler
        init_scheduler(app)

    @app.get("/api/health")
    def health_check():
        return {"status": "ok", "service": "GrantThrive API"}, 200

    return app


@login_manager.user_loader
def load_user(user_id: str):
    from app.models import User
    return db.session.get(User, int(user_id))