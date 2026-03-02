"""
GrantThrive — Application Configuration
=========================================
Configuration classes for development, testing, and production environments.

Usage in application factory::

    from config.config import config_by_name
    app.config.from_object(config_by_name[os.environ.get('FLASK_ENV', 'development')])

Environment variables (see .env.example for full reference):
  SECRET_KEY          — Required in production. Must be a long random string.
  DATABASE_URL        — SQLAlchemy database URI.
  MAIL_SERVER         — SMTP server hostname.
  MAIL_PORT           — SMTP port (default: 587).
  MAIL_USE_TLS        — Enable STARTTLS (default: true).
  MAIL_USERNAME       — SMTP authentication username.
  MAIL_PASSWORD       — SMTP authentication password.
  MAIL_DEFAULT_SENDER — From address for outgoing emails.
  UPLOAD_FOLDER       — Directory for uploaded files.
  REPORTS_OUTPUT_DIR  — Directory for generated PDF reports.
"""

import os


class Config:
    """Base configuration shared by all environments."""

    # ── Core ──────────────────────────────────────────────────────────────────
    # IMPORTANT: Override this with a strong random value in production.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
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
        "pool_pre_ping": True,   # Reconnect automatically after idle timeout
        "pool_recycle":  300,    # Recycle connections every 5 minutes
    }

    # ── Mail ──────────────────────────────────────────────────────────────────
    MAIL_SERVER          = os.environ.get("MAIL_SERVER",          "smtp.sendgrid.net")
    MAIL_PORT            = int(os.environ.get("MAIL_PORT",        587))
    MAIL_USE_TLS         = os.environ.get("MAIL_USE_TLS",         "true").lower() == "true"
    MAIL_USERNAME        = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD        = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER  = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@grantthrive.com"
    )

    # ── File uploads ──────────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB hard limit (enforced by Flask)
    UPLOAD_FOLDER      = os.environ.get("UPLOAD_FOLDER", "/tmp/grantthrive_uploads")

    # Whitelist of allowed file extensions for grant application documents.
    # Any upload whose extension is not in this set will be rejected with 400.
    UPLOAD_ALLOWED_EXTENSIONS = {
        "pdf", "doc", "docx",          # Documents
        "xls", "xlsx",                 # Spreadsheets
        "png", "jpg", "jpeg", "gif",   # Images
        "zip",                         # Archives (e.g. supporting materials)
    }

    # ── Reports ───────────────────────────────────────────────────────────────
    REPORTS_OUTPUT_DIR = os.environ.get(
        "REPORTS_OUTPUT_DIR",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports_output"),
    )


class DevelopmentConfig(Config):
    """Development configuration — enables debug mode and uses a local SQLite DB."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL", "sqlite:///grantthrive_dev.db"
    )


class TestingConfig(Config):
    """Testing configuration — uses an in-memory SQLite DB and suppresses email."""

    TESTING               = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED      = False
    MAIL_SUPPRESS_SEND    = True


class ProductionConfig(Config):
    """Production configuration.

    The application factory (``app/__init__.py``) will raise a ``RuntimeError``
    at startup if ``SECRET_KEY`` is still set to the insecure default value.
    """
    pass


# ── Convenience mapping ───────────────────────────────────────────────────────

config_by_name = {
    "development": DevelopmentConfig,
    "testing":     TestingConfig,
    "production":  ProductionConfig,
}
