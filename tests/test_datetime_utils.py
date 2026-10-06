from datetime import datetime, timezone

import pytest

from app.common.datetime_utils import parse_api_datetime, utc_iso


def test_parse_api_datetime_normalises_offset_to_naive_utc():
    parsed = parse_api_datetime("2026-10-06T21:00:00+11:00")
    assert parsed == datetime(2026, 10, 6, 10, 0, 0)
    assert parsed.tzinfo is None


def test_parse_api_datetime_accepts_z_suffix():
    assert parse_api_datetime("2026-10-06T10:00:00Z") == datetime(2026, 10, 6, 10, 0, 0)


def test_parse_api_datetime_treats_legacy_naive_value_as_utc():
    assert parse_api_datetime("2026-10-06T10:00:00") == datetime(2026, 10, 6, 10, 0, 0)


def test_parse_api_datetime_rejects_missing_or_invalid_value():
    with pytest.raises(ValueError):
        parse_api_datetime("")
    with pytest.raises(ValueError):
        parse_api_datetime("not-a-date")


def test_utc_iso_marks_naive_database_values_as_utc():
    assert utc_iso(datetime(2026, 10, 6, 10, 0, 0)) == "2026-10-06T10:00:00Z"


def test_utc_iso_normalises_aware_values_to_utc():
    source = datetime(2026, 10, 6, 21, 0, 0, tzinfo=timezone.utc)
    assert utc_iso(source) == "2026-10-06T21:00:00Z"
