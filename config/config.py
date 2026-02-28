"""
GrantThrive — Application Configuration
"""
import os


class Config:
    """Base configuration."""

    # ── Core ──────────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG      = False
    TESTING    = False

    # ── Database ──────────────────────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///grantthrive.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle":  300,
    }

    # ── Mail ──────────────────────────────────────────────────────────────────
    MAIL_SERVER   = os.environ.get("MAIL_SERVER",   "smtp.sendgrid.net")
    MAIL_PORT     = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS  = os.environ.get("MAIL_USE_TLS",  "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@grantthrive.com.au"
    )

    # ── File uploads ──────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    UPLOAD_FOLDER      = os.environ.get("UPLOAD_FOLDER", "/tmp/grantthrive_uploads")

    # ── Reports ───────────────────────────────────────────────────────────────
    REPORTS_OUTPUT_DIR = os.environ.get(
        "REPORTS_OUTPUT_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports_output"),
    )


class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite:///grantthrive_dev.db"
    )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True


class ProductionConfig(Config):
    pass


config_by_name = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
}
