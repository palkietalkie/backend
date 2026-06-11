"""Tests for POST /integrations/apple-calendar/events.

iOS pushes EventKit events; the route fans each one out into an 'apple_calendar_event' row in the events analytics table so conversation-start can read them back. Assertions exercise the JSON shape persisted into props."""

from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_persists_one_event_row_per_pushed_event(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    start = datetime.now(UTC)
    resp = await client.post(
        "/integrations/apple-calendar/events",
        json=[
            {
                "title": "Standup",
                "start": start.isoformat(),
                "end": (start + timedelta(minutes=15)).isoformat(),
                "location": "Zoom",
            },
            {
                "title": "Lunch with Naoto",
                "start": (start + timedelta(hours=4)).isoformat(),
            },
        ],
    )
    assert resp.status_code == 204
    rows = await db.fetch(
        """SELECT props FROM events
           WHERE user_id = $1 AND event_type = 'apple_calendar_event'
           ORDER BY props->>'title'""",
        user["id"],
    )
    assert len(rows) == 2
    lunch, standup = rows
    assert standup["props"]["title"] == "Standup"
    assert standup["props"]["location"] == "Zoom"
    assert standup["props"]["start"] == start.isoformat()
    assert standup["props"]["end"] == (start + timedelta(minutes=15)).isoformat()
    # Optional fields collapse to null when omitted by the client.
    assert lunch["props"]["title"] == "Lunch with Naoto"
    assert lunch["props"]["end"] is None
    assert lunch["props"]["location"] is None


async def test_empty_list_writes_nothing_and_still_204(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.post("/integrations/apple-calendar/events", json=[])
    assert resp.status_code == 204
    count = await db.fetchval(
        """SELECT COUNT(*) FROM events
           WHERE user_id = $1 AND event_type = 'apple_calendar_event'""",
        user["id"],
    )
    assert count == 0


async def test_missing_required_title_is_422(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/integrations/apple-calendar/events",
        json=[{"start": datetime.now(UTC).isoformat()}],
    )
    assert resp.status_code == 422
