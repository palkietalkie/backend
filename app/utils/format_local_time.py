from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def format_local_time(tz_name: str | None) -> str:
    """Best-effort local-time label using zoneinfo if available; else UTC."""
    if tz_name:
        try:
            now = datetime.now(ZoneInfo(tz_name))
            return now.strftime("%A %H:%M %Z")
        except ZoneInfoNotFoundError:
            return datetime.now(UTC).strftime("%A %H:%M UTC")
    return datetime.now(UTC).strftime("%A %H:%M UTC")
