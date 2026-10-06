"""Consistent password-strength policy for GrantThrive account credentials."""
from __future__ import annotations

import re

MIN_PASSWORD_LENGTH = 10
_PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).+$")
PASSWORD_REQUIREMENTS = (
    "Password must be at least 10 characters and include an uppercase letter, "
    "a lowercase letter, a number, and a special character."
)


def password_error(password: str) -> str | None:
    """Return a single safe validation error, or ``None`` when the password is strong."""
    if not isinstance(password, str) or len(password) < MIN_PASSWORD_LENGTH:
        return PASSWORD_REQUIREMENTS
    if not _PASSWORD_PATTERN.match(password):
        return PASSWORD_REQUIREMENTS
    return None
