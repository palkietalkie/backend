from datetime import UTC, timedelta

from app.routers.entitlement.compute_local_day_window import compute_local_day_window


def test_window_is_24_hours() -> None:
    start, end = compute_local_day_window("America/Los_Angeles")
    assert end - start == timedelta(days=1)
    # Returned as UTC-aware regardless of the requested zone.
    assert start.tzinfo == UTC
    assert end.tzinfo == UTC


def test_none_timezone_falls_back_to_utc() -> None:
    start, _end = compute_local_day_window(None)
    assert start.tzinfo == UTC
    # In UTC, the local-day start equals UTC midnight.
    assert start.hour == 0 and start.minute == 0


def test_tokyo_window_starts_at_tokyo_midnight_uts() -> None:
    start, _end = compute_local_day_window("Asia/Tokyo")
    # Tokyo midnight is 15:00 UTC the previous day. Loose check on the UTC time.
    assert start.hour == 15


def test_legacy_alias_us_pacific_resolves() -> None:
    # The exact key iOS sent that 500'd prod: the slim runtime lacked the tz "backward" links so ZoneInfo("US/Pacific") raised. The tzdata dependency must make this legacy alias resolve to actual Pacific time, NOT silently fall back to UTC. Pacific midnight is 07:00 (PDT) or 08:00 (PST) UTC; a UTC fallback would show hour 0.
    start, _end = compute_local_day_window("US/Pacific")
    assert start.hour in (7, 8)


def test_unresolvable_timezone_falls_back_to_utc() -> None:
    # Backstop: a garbage/unknown tz string must degrade to a UTC window, never raise — the free-plan check can't 500 conversation start over a timezone.
    start, _end = compute_local_day_window("Not/ARealZone")
    assert start.tzinfo == UTC
    assert start.hour == 0 and start.minute == 0
