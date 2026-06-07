"""Provider-neutral calendar event payload.

Shared between Google / Apple / Outlook providers. Used by the conversation-start prompt assembly to surface "today's calendar" context naturally to the persona."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: datetime
    end: datetime | None
    location: str | None
