from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo


def compute_local_day_window(tz_name: str | None) -> tuple[datetime, datetime]:
    # [start_of_local_day, end_of_local_day) as UTC-aware datetimes.
    tz = ZoneInfo(tz_name) if tz_name else UTC
    now_local = datetime.now(tz)
    start_local = datetime.combine(now_local.date(), time.min, tzinfo=tz)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)
