"""Datetime helpers for API boundaries.

PostgreSQL columns in this application currently use ``timestamp without time
zone``.  All API date-times are therefore normalised to UTC before persisting
and explicitly marked as UTC when serialised.
"""
from __future__ import annotations

from datetime import datetime, timezone


def parse_api_datetime(value: str) -> datetime:
    """Parse an ISO-8601 value and return a UTC-naive database value.

    A value carrying an offset (including ``Z``) is converted to UTC first;
    a timezone-free value is treated as UTC for backwards compatibility with
    existing form payloads.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("A date-time value is required.")

    parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def utc_iso(value: datetime | None) -> str | None:
    """Serialise a database datetime as an explicit UTC ISO-8601 string."""
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)
    return value.isoformat().replace("+00:00", "Z")
