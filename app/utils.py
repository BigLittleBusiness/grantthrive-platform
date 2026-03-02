"""
GrantThrive — Legacy Utility Shim
===================================
.. deprecated::
   This module is kept only for backwards compatibility while the codebase is
   migrated to the ``app.common`` package.  New code should import directly
   from the appropriate ``app.common.*`` module:

   - ``app.common.decorators``  — JWT auth decorators
   - ``app.common.formatters``  — Display helpers (currency, dates, status)
   - ``app.common.validators``  — Input validation helpers
   - ``app.common.pagination``  — Query pagination helpers

This file will be removed once all internal imports have been updated.
"""

# Re-export everything so existing imports continue to work unchanged.
from app.common.decorators import token_required, role_required  # noqa: F401
from app.common.formatters import (  # noqa: F401
    format_currency,
    format_date,
    format_datetime,
    get_time_ago,
    calculate_days_until,
    get_status_badge_class,
    format_status_display,
    calculate_percentage,
    calculate_file_size_mb,
    truncate_text,
    register_template_filters,
)
from app.common.validators import (  # noqa: F401
    validate_email,
    validate_phone,
    validate_date_range,
    get_file_extension,
    is_allowed_file,
    sanitize_filename,
)
from app.common.pagination import (  # noqa: F401
    paginate_results,
    build_search_query,
)

# ── Legacy Flask-Login-based decorators (kept for backwards compat) ────────────
# These are no longer used by any route in the codebase — all routes now use
# the JWT-based ``token_required`` / ``role_required`` decorators above.
# They are retained here only to prevent ImportError if any third-party code
# or test still references them.  They will be removed in a future cleanup.

from functools import wraps
from flask import jsonify

try:
    from flask_login import current_user as _current_user

    def admin_required(f):
        """Legacy Flask-Login admin decorator. Use ``role_required`` instead."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not _current_user.is_authenticated or not _current_user.is_admin():
                return jsonify({"error": "Admin access required"}), 403
            return f(*args, **kwargs)
        return decorated

    def staff_required(f):
        """Legacy Flask-Login staff decorator. Use ``role_required`` instead."""
        @wraps(f)
        def decorated(*args, **kwargs):
            if not _current_user.is_authenticated or not _current_user.is_staff():
                return jsonify({"error": "Staff access required"}), 403
            return f(*args, **kwargs)
        return decorated

except ImportError:
    pass  # Flask-Login not installed — legacy decorators unavailable


# ── Misc helpers that have no common-package equivalent yet ───────────────────

import hashlib
import secrets
from flask import request, current_app


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure URL-safe random token."""
    return secrets.token_urlsafe(length)


def hash_file_content(content: bytes) -> str:
    """Return the SHA-256 hex digest of *content*."""
    return hashlib.sha256(content).hexdigest()


def get_client_ip() -> str:
    """Return the client's IP address, respecting ``X-Forwarded-For`` headers."""
    forwarded = request.environ.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        # Take the first IP in the chain (the original client)
        return forwarded.split(",")[0].strip()
    return request.environ.get("REMOTE_ADDR", "unknown")


def log_user_action(action: str, details: str | None = None) -> None:
    """Write an entry to the ``audit_logs`` table.

    Args:
        action:  Short action label, e.g. ``'login'``, ``'password_changed'``.
        details: Optional free-text detail string.
    """
    from app.models import AuditLog
    from app import db
    from datetime import datetime, timezone

    try:
        from flask_login import current_user as _cu
        user_id = _cu.id if _cu.is_authenticated else None
    except Exception:
        user_id = None

    try:
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type="system",
            entity_id=0,
            ip_address=get_client_ip(),
            user_agent=request.headers.get("User-Agent", ""),
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as exc:
        current_app.logger.error("Failed to log user action '%s': %s", action, exc)


def generate_qr_code_data_url(data: str) -> str:
    """Generate a QR code for *data* and return it as a base64 PNG data URL."""
    import qrcode
    import io
    import base64

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_data = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/png;base64,{img_data}"
