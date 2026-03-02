"""
GrantThrive — Input Validators
================================
Pure validation functions for user-supplied input.

All functions return a boolean (or a ``(bool, str | None)`` tuple for
validators that also return an error message).
"""

import re
from datetime import datetime


# ── Contact details ───────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def validate_email(email: str) -> bool:
    """Return ``True`` if *email* matches a valid email address pattern."""
    return bool(_EMAIL_RE.match(email or ""))


def validate_phone(phone: str) -> bool:
    """Return ``True`` if *phone* is a valid Australian or New Zealand number.

    Accepts numbers with spaces, hyphens, and parentheses.  Internally
    normalises to digits only before checking length and prefix rules.

    Supported formats:
    - Australian mobile:   04xx xxx xxx  (10 digits, starts with 04)
    - Australian landline: 0x xxxx xxxx  (10 digits, starts with 02/03/07/08)
    - NZ mobile:           02x xxx xxxx  (10 digits, starts with 02)
    - NZ landline:         0x xxx xxxx   (9–10 digits, starts with 03/04/06/07/09)
    """
    digits = re.sub(r"\D", "", phone or "")

    if len(digits) == 10:
        return digits.startswith(("02", "03", "04", "07", "08"))
    if len(digits) == 9:
        return digits.startswith(("03", "04", "06", "07", "09"))
    return False


# ── Date ranges ───────────────────────────────────────────────────────────────

def validate_date_range(
    start_date: datetime | None,
    end_date: datetime | None,
    max_days: int = 3650,
) -> tuple[bool, str | None]:
    """Validate that *start_date* is before *end_date* and within *max_days*.

    Args:
        start_date: Start of the date range.
        end_date:   End of the date range.
        max_days:   Maximum allowed span in days (default: 10 years / 3650 days).

    Returns:
        ``(True, None)`` if valid, or ``(False, error_message)`` if not.
    """
    if start_date and end_date:
        if start_date > end_date:
            return False, "Start date must be before end date."
        if (end_date - start_date).days > max_days:
            return False, f"Date range cannot exceed {max_days // 365} years."
    return True, None


# ── File uploads ──────────────────────────────────────────────────────────────

def get_file_extension(filename: str) -> str:
    """Return the lowercase file extension of *filename* (without the dot).

    Returns an empty string if there is no extension.
    """
    return filename.rsplit(".", 1)[1].lower() if "." in filename else ""


def is_allowed_file(filename: str, allowed_extensions: set[str]) -> bool:
    """Return ``True`` if *filename* has an extension in *allowed_extensions*.

    Args:
        filename:           Original filename from the upload.
        allowed_extensions: Set of lowercase extensions without dots,
                            e.g. ``{'pdf', 'docx', 'png'}``.
    """
    return get_file_extension(filename) in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage on disk.

    - Strips directory components (path traversal protection).
    - Replaces characters outside ``[A-Za-z0-9_\\-.]`` with underscores.
    - Truncates the base name to 100 characters.

    Args:
        filename: Original filename from the upload.

    Returns:
        Safe filename string.
    """
    # Strip path components
    filename = filename.split("/")[-1].split("\\")[-1]

    # Replace unsafe characters
    filename = re.sub(r"[^\w\-_\.]", "_", filename)

    # Truncate base name
    if "." in filename:
        name, ext = filename.rsplit(".", 1)
        name = name[:100]
        return f"{name}.{ext}"
    return filename[:100]
