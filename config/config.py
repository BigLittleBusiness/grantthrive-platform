"""
GrantThrive — Application Configuration
=========================================

Configuration classes for development, testing, and production environments.

Usage in application factory:

    from config.config import config_by_name
    app.config.from_object(config_by_name[os.environ.get("FLASK_ENV", "development")])

Environment variables (.env):

  SECRET_KEY
  DATABASE_URL
  DEV_DATABASE_URL
  TEST_DATABASE_URL

Example PostgreSQL connection:

  DATABASE_URL=postgresql://granthrive_user:password@localhost:5432/granthrive
"""

import os
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


def _fix_postgres_url(url: str) -> str:
    """
    Some hosting providers supply DATABASE_URL with the legacy
    "postgres://" scheme. SQLAlchemy requires "postgresql://".
    """
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    """Base configuration shared by all environments."""

    # ─────────────────────────────────────────
    # Core
    # ─────────────────────────────────────────

    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")

    DEBUG = False
    TESTING = False

    # ─────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────

    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("DATABASE_URL")
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

    # ─────────────────────────────────────────
    # Mail
    # ─────────────────────────────────────────

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.sendgrid.net")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))

    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"

    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER",
        "noreply@grantthrive.com"
    )

    # ─────────────────────────────────────────
    # File Uploads & S3 Storage
    # ─────────────────────────────────────────

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # Local upload folder (legacy/fallback for development)
    UPLOAD_FOLDER = os.environ.get(
        "UPLOAD_FOLDER",
        "/tmp/grantthrive_uploads"
    )

    UPLOAD_ALLOWED_EXTENSIONS = {
        "pdf",
        "doc",
        "docx",
        "xls",
        "xlsx",
        "png",
        "jpg",
        "jpeg",
        "gif",
        "zip",
    }

    # AWS S3 Configuration
    AWS_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")
    AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET")
    AWS_S3_USE_LOCAL_FALLBACK = os.environ.get("AWS_S3_USE_LOCAL_FALLBACK", "false").lower() == "true"

    # ─────────────────────────────────────────
    # AI / AWS Bedrock
    # ─────────────────────────────────────────
    # Safe-off by default. Enable only after Bedrock model access, a published
    # guardrail, privacy review, and pilot approval are in place.
    AI_FEATURES_ENABLED = os.environ.get("AI_FEATURES_ENABLED", "false").lower() == "true"
    AWS_BEDROCK_MODEL_ID = os.environ.get("AWS_BEDROCK_MODEL_ID")
    AWS_BEDROCK_GUARDRAIL_ID = os.environ.get("AWS_BEDROCK_GUARDRAIL_ID")
    AWS_BEDROCK_GUARDRAIL_VERSION = os.environ.get("AWS_BEDROCK_GUARDRAIL_VERSION")
    AWS_BEDROCK_MAX_TOKENS = int(os.environ.get("AWS_BEDROCK_MAX_TOKENS", "900"))
    AWS_BEDROCK_TEMPERATURE = float(os.environ.get("AWS_BEDROCK_TEMPERATURE", "0.2"))

    # ─────────────────────────────────────────
    # Reports
    # ─────────────────────────────────────────

    # Local reports output directory (legacy/fallback for development)
    REPORTS_OUTPUT_DIR = os.environ.get(
        "REPORTS_OUTPUT_DIR",
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "reports_output"
        ),
    )


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True

    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("DEV_DATABASE_URL")
        or os.environ.get("DATABASE_URL")
        or "postgresql://localhost/granthrive_dev"
    )

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True

    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("TEST_DATABASE_URL")
        or "postgresql://localhost/granthrive_test"
    )

    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 2,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }


class ProductionConfig(Config):
    """Production configuration."""

    pass


# Environment mapping

config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}