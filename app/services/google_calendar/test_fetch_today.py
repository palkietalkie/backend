"""Tests for google_calendar.fetch_today — Google Calendar API mocked via respx."""

import uuid
from datetime import UTC, datetime

import httpx
import respx

from app.services.google_calendar.constants import EVENTS_URL
from app.services.google_calendar.fetch_today import fetch_today
from app.services.neon.rows import CalendarTokenRow


def _token() -> CalendarTokenRow:
    now = datetime.now(UTC)
    return CalendarTokenRow(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider="google",
        access_token="at",
        refresh_token=None,
        expires_at=None,
        created_at=now,
        updated_at=now,
    )


@respx.mock
async def test_fetch_today_returns_parsed_events() -> None:
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "summary": "Standup",
                        "start": {"dateTime": "2026-06-05T09:00:00-07:00"},
                        "end": {"dateTime": "2026-06-05T09:15:00-07:00"},
                    }
                ]
            },
        )
    )
    events = await fetch_today(_token())
    assert len(events) == 1
    assert events[0].title == "Standup"


@respx.mock
async def test_fetch_today_skips_unparseable_items() -> None:
    respx.get(EVENTS_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"summary": "No start"},
                    {
                        "summary": "Good",
                        "start": {"dateTime": "2026-06-05T09:00:00-07:00"},
                        "end": {"dateTime": "2026-06-05T09:15:00-07:00"},
                    },
                ]
            },
        )
    )
    events = await fetch_today(_token())
    assert [e.title for e in events] == ["Good"]


@respx.mock
async def test_fetch_today_includes_authorization_header() -> None:
    route = respx.get(EVENTS_URL).mock(return_value=httpx.Response(200, json={"items": []}))
    await fetch_today(_token())
    assert route.calls.last.request.headers["authorization"] == "Bearer at"
