import httpx

from app.services.calendar.event import CalendarEvent
from app.services.google_calendar.compute_today_window import compute_today_window
from app.services.google_calendar.constants import EVENTS_URL, MAX_RESULTS
from app.services.google_calendar.parse_event import parse_event
from app.services.neon.rows import CalendarTokenRow


async def fetch_today(token: CalendarTokenRow) -> list[CalendarEvent]:
    start_of_day, end_of_day = compute_today_window()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            EVENTS_URL,
            headers={"Authorization": f"Bearer {token['access_token']}"},
            params={
                "timeMin": start_of_day.isoformat(),
                "timeMax": end_of_day.isoformat(),
                "singleEvents": "true",
                "orderBy": "startTime",
                "maxResults": MAX_RESULTS,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    events: list[CalendarEvent] = []
    for item in data.get("items", []):
        parsed = parse_event(item)
        if parsed is not None:
            events.append(parsed)
    return events
