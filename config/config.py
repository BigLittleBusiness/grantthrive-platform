"""
GrantThrive — Application Configuration
=========================================
Configuration classes for development, testing, and production environments.

Usage in application factory::

    from config.config import config_by_name
    app.config.from_object(config_by_name[os.environ.get('FLASK_ENV', 'development')])

Environment variables (see .env.example for full reference):
  SECRET_KEY          — Required in production. Must be a long random string.
  DATABASE_URL        — PostgreSQL connection URI.
                        Format: postgresql://user:password@host:port/dbname
                        Also accepts the legacy "postgres://" prefix used by
                        some hosting providers (auto-corrected to "postgresql://").
  DEV_DATABASE_URL    — PostgreSQL URI for local development (optional).
  TEST_DATABASE_URL   — PostgreSQL URI for the test environment (optional).
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


def _fix_postgres_url(url: str) -> str:
    """
    Some hosting providers (e.g. Heroku, Render) supply DATABASE_URL with the
    legacy ``postgres://`` scheme.  SQLAlchemy 1.4+ requires ``postgresql://``.
    This helper corrects the scheme transparently.
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration shared by all environments."""

    # ── Core ──────────────────────────────────────────────────────────────────
    # IMPORTANT: Override this with a strong random value in production.
    # Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEBUG      = False
    TESTING    = False

    # ── Database ──────────────────────────────────────────────────────────────
    # PostgreSQL is the required database engine for all environments.
    # The DATABASE_URL environment variable must be set to a valid PostgreSQL
    # connection URI before starting the application.
    #
    # Example:
    #   DATABASE_URL=postgresql://grantthrive:password@localhost:5432/grantthrive
    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("DATABASE_URL", "postgresql://localhost/grantthrive")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool tuned for a multi-tenant SaaS workload.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size":     10,
        "max_overflow":  20,
        "pool_timeout":  30,
        "pool_recycle":  1800,   # 30 minutes
        "pool_pre_ping": True,
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
    """Development configuration — enables debug mode and uses a local PostgreSQL DB."""

    DEBUG = True
    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("DEV_DATABASE_URL", "postgresql://localhost/grantthrive_dev")
    )
    # Smaller pool for local development.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size":     5,
        "max_overflow":  10,
        "pool_timeout":  30,
        "pool_recycle":  1800,
        "pool_pre_ping": True,
    }


class TestingConfig(Config):
    """Testing configuration — uses a dedicated PostgreSQL test DB and suppresses email."""

    TESTING               = True
    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/grantthrive_test")
    )
    WTF_CSRF_ENABLED      = False
    MAIL_SUPPRESS_SEND    = True
    # Minimal pool for CI/test runners.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size":     2,
        "max_overflow":  5,
        "pool_timeout":  10,
        "pool_recycle":  300,
        "pool_pre_ping": True,
    }


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
