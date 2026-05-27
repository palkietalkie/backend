from datetime import datetime
from typing import Any

from app.services.calendar.event import CalendarEvent


def parse_event(item: dict[str, Any]) -> CalendarEvent | None:
    title = item.get("summary", "(no title)")
    start_raw = (item.get("start") or {}).get("dateTime") or (
        item.get("start") or {}
    ).get("date")
    end_raw = (item.get("end") or {}).get("dateTime") or (item.get("end") or {}).get(
        "date"
    )
    if not start_raw:
        return None
    try:
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end = (
            datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else None
        )
    except ValueError:
        return None
    return CalendarEvent(
        title=title, start=start, end=end, location=item.get("location")
    )
