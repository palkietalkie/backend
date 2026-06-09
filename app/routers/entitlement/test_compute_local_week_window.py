"""Tests the [Mon 00:00, next Mon 00:00) week window. ISO week (Monday-start) — critical for the 30 min/week free-plan cap rolling over consistently across timezones."""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.routers.entitlement.compute_local_week_window import compute_local_week_window


def test_window_is_seven_days_wide() -> None:
    start, end = compute_local_week_window("UTC")
    assert end - start == timedelta(days=7)


def test_window_starts_on_monday_local() -> None:
    for tz in ("UTC", "Asia/Tokyo", "America/Los_Angeles", "Europe/Berlin"):
        start, _end = compute_local_week_window(tz)
        local_start = start.astimezone(ZoneInfo(tz))
        assert local_start.weekday() == 0, (
            f"{tz}: start.weekday()={local_start.weekday()} (want 0=Mon)"
        )
        assert local_start.hour == 0 and local_start.minute == 0


def test_window_contains_now() -> None:
    start, end = compute_local_week_window("UTC")
    now = datetime.now(UTC)
    assert start <= now < end


def test_none_timezone_falls_back_to_utc() -> None:
    start, _end = compute_local_week_window(None)
    assert start.tzinfo is UTC
