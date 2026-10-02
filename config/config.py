"""
GrantThrive — Application Configuration
=========================================
`Config` is loaded by create_app(); `TestingConfig` is used by the test suite.
Every environment variable read by the backend is documented in .env.example.

Settings read directly from the environment by the modules that use them
(not mirrored here): FIELD_ENCRYPTION_KEY / FIELD_HMAC_KEY (common/encryption),
SYSTEM_CONFIG_ENCRYPTION_KEY (models.SystemConfig), ABR_GUID (common/abr_service),
AWS_* and FRONTEND_BASE_URL / MARKETING_BASE_URL (common/email_service,
common/s3_service), REDIS_URL (app/__init__).
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


def _flag(name: str, default: str) -> bool:
    return os.environ.get(name, default).lower() == "true"


class Config:
    """Configuration loaded by create_app()."""

    # ─────────────────────────────────────────
    # Core
    # ─────────────────────────────────────────

    # Required — signs JWTs. create_app() refuses to start without it.
    SECRET_KEY = os.environ.get("SECRET_KEY", "")

    # "development" enables developer-only features (demo login).
    # Anything else — including unset — is treated as production.
    FLASK_ENV = os.environ.get("FLASK_ENV", "production")

    DEBUG = False
    TESTING = False

    # Public URL of the frontend: links in emails, Stripe Checkout/Portal returns.
    FRONTEND_BASE_URL = os.environ.get("FRONTEND_BASE_URL", "https://app.grantthrive.com").rstrip("/")

    # ─────────────────────────────────────────
    # Database (PostgreSQL)
    # ─────────────────────────────────────────

    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(os.environ.get("DATABASE_URL"))
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,
        "pool_pre_ping": True,
    }

    # Maximum request size (document uploads)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ─────────────────────────────────────────
    # Public contact forms / Cloudflare Turnstile
    # ─────────────────────────────────────────
    TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY", "")
    TURNSTILE_EXPECTED_HOSTNAMES = os.environ.get("TURNSTILE_EXPECTED_HOSTNAMES", "")
    TURNSTILE_TEST_BYPASS = _flag("TURNSTILE_TEST_BYPASS", "false")
    # Submissions are stored in the database; this address receives a
    # content-free alert linking to the protected admin dashboard.
    ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "")
    ADMIN_DASHBOARD_URL = os.environ.get(
        "ADMIN_DASHBOARD_URL", "https://admin.grantthrive.com/admin/dashboard?tab=form-submissions"
    )
    PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED = _flag("PUBLIC_SUBMISSION_ENCRYPTION_REQUIRED", "true")

    # ─────────────────────────────────────────
    # Billing (Stripe)
    # ─────────────────────────────────────────
    # Prices are resolved by lookup key (see scripts/stripe_setup.py).
    STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PORTAL_CONFIGURATION_ID = os.environ.get("STRIPE_PORTAL_CONFIGURATION_ID", "")


class TestingConfig(Config):
    """Configuration for the automated test suite."""

    TESTING = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "test-secret-key"
    SQLALCHEMY_DATABASE_URI = _fix_postgres_url(
        os.environ.get("TEST_DATABASE_URL")
        or "postgresql://localhost/grantthrive_test"
    )
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 2,
        "max_overflow": 5,
        "pool_timeout": 10,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
