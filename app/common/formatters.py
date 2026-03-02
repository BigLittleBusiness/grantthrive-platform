"""
GrantThrive — Display Formatters
==================================
Pure helper functions for formatting values for display in API responses
and Jinja2 templates.

All functions are safe to call with ``None`` — they return a sensible
fallback string rather than raising an exception.
"""

from datetime import datetime, timezone


# ── Currency ──────────────────────────────────────────────────────────────────

def format_currency(amount, currency: str = "AUD") -> str:
    """Format a numeric amount as a currency string.

    Args:
        amount: Numeric value to format. ``None`` returns ``'N/A'``.
        currency: ISO 4217 currency code. AUD and NZD use the ``$`` symbol.

    Returns:
        Formatted string, e.g. ``'$1,234.56'``.
    """
    if amount is None:
        return "N/A"
    symbol = "$" if currency in ("AUD", "NZD") else currency
    return f"{symbol}{amount:,.2f}"


# ── Dates & times ─────────────────────────────────────────────────────────────

def format_date(date, fmt: str = "%d/%m/%Y") -> str:
    """Format a date or ISO-8601 date string for display.

    Args:
        date: A ``datetime`` object or ISO-8601 string. ``None`` returns ``'N/A'``.
        fmt: ``strftime`` format string.

    Returns:
        Formatted date string.
    """
    if date is None:
        return "N/A"
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            return date
    return date.strftime(fmt)


def format_datetime(dt, fmt: str = "%d/%m/%Y %I:%M %p") -> str:
    """Format a datetime or ISO-8601 datetime string for display.

    Args:
        dt: A ``datetime`` object or ISO-8601 string. ``None`` returns ``'N/A'``.
        fmt: ``strftime`` format string.

    Returns:
        Formatted datetime string.
    """
    if dt is None:
        return "N/A"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    return dt.strftime(fmt)


def get_time_ago(dt) -> str:
    """Return a human-readable relative time string (e.g. ``'3 days ago'``).

    Args:
        dt: A ``datetime`` object. ``None`` returns ``'Never'``.

    Returns:
        Relative time string.
    """
    if dt is None:
        return "Never"

    now = datetime.now(timezone.utc)
    # Handle both naive and aware datetimes
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt

    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "Just now"


def calculate_days_until(target_date) -> int | None:
    """Calculate the number of days until a target date.

    Args:
        target_date: A ``datetime`` object or ISO-8601 string.

    Returns:
        Integer number of days (may be negative if date has passed), or ``None``.
    """
    if target_date is None:
        return None
    if isinstance(target_date, str):
        try:
            target_date = datetime.fromisoformat(target_date)
        except ValueError:
            return None

    now = datetime.now(timezone.utc)
    if target_date.tzinfo is None:
        target_date = target_date.replace(tzinfo=timezone.utc)
    return (target_date - now).days


# ── Status labels ─────────────────────────────────────────────────────────────

_STATUS_BADGE_CLASSES = {
    "draft":        "bg-secondary",
    "submitted":    "bg-primary",
    "under_review": "bg-warning",
    "approved":     "bg-success",
    "rejected":     "bg-danger",
    "withdrawn":    "bg-dark",
    "open":         "bg-success",
    "closed":       "bg-danger",
    "pending":      "bg-warning",
    "completed":    "bg-success",
    "active":       "bg-success",
    "inactive":     "bg-secondary",
}


def get_status_badge_class(status: str) -> str:
    """Return the Bootstrap badge CSS class for a given status string.

    Args:
        status: Status string (case-insensitive).

    Returns:
        Bootstrap ``bg-*`` class string.
    """
    return _STATUS_BADGE_CLASSES.get((status or "").lower(), "bg-secondary")


def format_status_display(status: str) -> str:
    """Convert an underscore-separated status string to a human-readable label.

    Example: ``'under_review'`` → ``'Under Review'``
    """
    return (status or "").replace("_", " ").title()


# ── Numbers ───────────────────────────────────────────────────────────────────

def calculate_percentage(part, total) -> float:
    """Calculate a percentage, guarding against division by zero.

    Returns:
        Rounded percentage (1 decimal place), or ``0`` if ``total`` is zero.
    """
    if not total:
        return 0
    return round((part / total) * 100, 1)


def calculate_file_size_mb(size_bytes: int) -> float:
    """Convert a byte count to megabytes (rounded to 2 decimal places)."""
    return round(size_bytes / (1024 * 1024), 2)


# ── Text ──────────────────────────────────────────────────────────────────────

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate a string to ``max_length`` characters, appending ``suffix``.

    Args:
        text: Input string. ``None`` returns ``''``.
        max_length: Maximum total length of the returned string (including suffix).
        suffix: String appended when truncation occurs.

    Returns:
        Truncated string.
    """
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


# ── Template filter registration ──────────────────────────────────────────────

def register_template_filters(app) -> None:
    """Register all formatter functions as Jinja2 template filters.

    Call this once during application factory setup::

        from app.common.formatters import register_template_filters
        register_template_filters(app)
    """

    @app.template_filter("currency")
    def _currency(amount, currency="AUD"):
        return format_currency(amount, currency)

    @app.template_filter("date")
    def _date(date, fmt="%d/%m/%Y"):
        return format_date(date, fmt)

    @app.template_filter("datetime")
    def _datetime(dt, fmt="%d/%m/%Y %I:%M %p"):
        return format_datetime(dt, fmt)

    @app.template_filter("truncate_text")
    def _truncate(text, length=100):
        return truncate_text(text, length)

    @app.template_filter("percentage")
    def _percentage(part, total):
        return calculate_percentage(part, total)

    @app.template_filter("status_badge")
    def _status_badge(status):
        return get_status_badge_class(status)

    @app.template_filter("status_display")
    def _status_display(status):
        return format_status_display(status)

    @app.template_filter("time_ago")
    def _time_ago(dt):
        return get_time_ago(dt)
