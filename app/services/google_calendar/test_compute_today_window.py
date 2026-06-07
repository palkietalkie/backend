from datetime import UTC, timedelta

from app.services.google_calendar.compute_today_window import compute_today_window


def test_window_is_24_hours_and_utc_aligned() -> None:
    start, end = compute_today_window()
    assert end - start == timedelta(days=1)
    assert start.tzinfo == UTC
    assert end.tzinfo == UTC
    assert start.hour == 0 and start.minute == 0 and start.second == 0
