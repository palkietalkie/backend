from datetime import UTC, datetime, time, timedelta


def compute_today_window() -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    start_of_day = datetime.combine(now.date(), time.min, tzinfo=UTC)
    end_of_day = start_of_day + timedelta(days=1)
    return start_of_day, end_of_day
