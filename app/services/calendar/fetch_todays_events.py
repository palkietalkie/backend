"""Multi-provider calendar fanout.

Walks a user's ``calendar_tokens`` rows, refreshes Google tokens on expiry, fetches events from each connected provider, and returns the union. Provider-level failures are swallowed: calendar is best-effort context for the conversation-start prompt."""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.services.calendar.event import CalendarEvent
from app.services.google_calendar.fetch_today import fetch_today as fetch_google_today
from app.services.google_calendar.refresh_token import (
    refresh_token as refresh_google_token,
)
from app.services.neon.db_conn import DBConn
from app.services.neon.make_rows import make_calendar_token_row
from app.services.neon.rows import UserRow


async def fetch_todays_events(user: UserRow, db: DBConn) -> list[CalendarEvent]:
    """Return today's calendar events across all connected providers."""
    rows = await db.fetch(
        """SELECT id, user_id, provider, access_token, refresh_token, expires_at, created_at, updated_at
           FROM calendar_tokens
           WHERE user_id = $1""",
        user["id"],
    )
    tokens = [make_calendar_token_row(row) for row in rows]
    out: list[CalendarEvent] = []
    for token in tokens:
        try:
            if token["provider"] == "google":
                if token["expires_at"] and token["expires_at"] <= datetime.now(UTC):
                    await refresh_google_token(token, db)
                out.extend(await fetch_google_today(token))
            # apple / outlook providers: TODO
        except httpx.HTTPError:
            continue
    return out
