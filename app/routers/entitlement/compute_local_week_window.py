from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo


def compute_local_week_window(tz_name: str | None) -> tuple[datetime, datetime]:
    """`[start_of_local_week, end_of_local_week)` as UTC-aware datetimes. Week starts Monday 00:00 in the user's timezone (ISO 8601 convention; matches what most non-US locales expect)."""
    tz = ZoneInfo(tz_name) if tz_name else UTC
    now_local = datetime.now(tz)
    today_start = datetime.combine(now_local.date(), time.min, tzinfo=tz)
    monday_local = today_start - timedelta(days=now_local.weekday())
    next_monday_local = monday_local + timedelta(days=7)
    return monday_local.astimezone(UTC), next_monday_local.astimezone(UTC)
