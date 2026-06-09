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
