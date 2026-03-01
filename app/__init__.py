from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_cors import CORS
from config.config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_class=Config):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # ── CORS: allow all GrantThrive subdomains (grantthrive.com) ─────────────
    # All five UI apps are served from subdomains of grantthrive.com and share
    # the same JWT-based SSO session.  In development, localhost ports are also
    # permitted.  The wildcard origin ("*") is intentionally NOT used so that
    # supports_credentials=True works correctly (browsers reject wildcard + credentials).
    allowed_origins = app.config.get("CORS_ORIGINS", [
        # Production
        "https://grantthrive.com",
        "https://app.grantthrive.com",
        "https://admin.grantthrive.com",
        "https://map.grantthrive.com",
        "https://roi.grantthrive.com",
        # Local development (Vite default ports for each app)
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:3000",
    ])
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # Initialize performance optimizations
    try:
        from app.optimizations import init_optimizations, PerformanceMiddleware, optimize_db_connection
        init_optimizations(app)
        PerformanceMiddleware(app)
        optimize_db_connection(app)
    except ImportError:
        pass  # Optimizations not available

    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    from app.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.grants import bp as grants_bp
    app.register_blueprint(grants_bp, url_prefix='/grants')

    from app.applications import bp as applications_bp
    app.register_blueprint(applications_bp, url_prefix='/applications')

    from app.reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp, url_prefix='/reviews')

    from app.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')

    from app.workflows import bp as workflows_bp
    app.register_blueprint(workflows_bp, url_prefix='/workflows')

    from app.voting import voting as voting_bp
    app.register_blueprint(voting_bp, url_prefix='/voting')

    from app.mapping import mapping as mapping_bp
    app.register_blueprint(mapping_bp, url_prefix='/mapping')

    from app.public import public as public_bp
    app.register_blueprint(public_bp, url_prefix='/public')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.api.health import health_bp
    app.register_blueprint(health_bp, url_prefix='/api')

    # Register template filters
    from app.utils import register_template_filters
    register_template_filters(app)

    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return User.query.get(int(user_id))
