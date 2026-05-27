from datetime import datetime
from typing import Any

from pydantic import BaseModel, ValidationError

from app.services.calendar.event import CalendarEvent


class _DateTimeOrDate(BaseModel):
    # camelCase intentional — matches Google Calendar v3's wire key. Suppress ruff's N815 since renaming would break deserialization.
    dateTime: str | None = None  # noqa: N815
    date: str | None = None


class _GoogleEvent(BaseModel):
    summary: str = "(no title)"
    start: _DateTimeOrDate | None = None
    end: _DateTimeOrDate | None = None
    location: str | None = None


def parse_event(item: dict[str, Any]) -> CalendarEvent | None:
    try:
        parsed = _GoogleEvent.model_validate(item)
    except ValidationError:
        return None
    if parsed.start is None:
        return None
    start_raw = parsed.start.dateTime or parsed.start.date
    end_raw = (parsed.end.dateTime or parsed.end.date) if parsed.end else None
    if start_raw is None:
        return None
    try:
        start = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_raw.replace("Z", "+00:00")) if end_raw else None
    except ValueError:
        return None
    return CalendarEvent(title=parsed.summary, start=start, end=end, location=parsed.location)
