"""Tests for the multi-provider calendar fanout."""

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import pytest

from app.services.calendar import fetch_todays_events as mod
from app.services.calendar.event import CalendarEvent
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import CalendarTokenRow, UserRow


async def _seed_token(
    db: DBConn,
    user_id: uuid.UUID,
    *,
    provider: str = "google",
    expires_at: datetime | None = None,
    refresh_token: str | None = "rt",
) -> None:
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        uuid.uuid4(),
        user_id,
        provider,
        "at",
        refresh_token,
        expires_at,
    )


async def test_fetch_todays_events_returns_empty_when_no_tokens(
    fake_user: UserRow, db: DBConn
) -> None:
    events = await mod.fetch_todays_events(fake_user, db)
    assert events == []


async def test_fetch_todays_events_calls_google_when_connected(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_token(db, fake_user["id"])
    sample = CalendarEvent(title="Standup", start=datetime.now(UTC), end=None, location=None)

    async def _fake_fetch(_token: CalendarTokenRow) -> list[CalendarEvent]:
        return [sample]

    monkeypatch.setattr(mod, "fetch_google_today", _fake_fetch)
    events = await mod.fetch_todays_events(fake_user, db)
    assert events == [sample]


async def test_fetch_todays_events_refreshes_expired_token(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    expired = datetime.now(UTC) - timedelta(minutes=1)
    await _seed_token(db, fake_user["id"], expires_at=expired)
    called = {"refresh": 0, "fetch": 0}

    async def _refresh(token: CalendarTokenRow, _db: DBConn) -> None:
        called["refresh"] += 1
        token["access_token"] = "refreshed"

    async def _fetch(_token: CalendarTokenRow) -> list[CalendarEvent]:
        called["fetch"] += 1
        return []

    monkeypatch.setattr(mod, "refresh_google_token", _refresh)
    monkeypatch.setattr(mod, "fetch_google_today", _fetch)
    await mod.fetch_todays_events(fake_user, db)
    assert called == {"refresh": 1, "fetch": 1}


async def test_fetch_todays_events_swallows_provider_errors(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_token(db, fake_user["id"])

    async def _boom(_token: CalendarTokenRow) -> list[CalendarEvent]:
        raise httpx.HTTPError("upstream 500")

    monkeypatch.setattr(mod, "fetch_google_today", _boom)
    events = await mod.fetch_todays_events(fake_user, db)
    assert events == []


async def test_fetch_todays_events_ignores_unknown_providers(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed_token(db, fake_user["id"], provider="apple")
    called: dict[str, int] = {"fetch": 0}

    async def _fetch(_token: CalendarTokenRow) -> list[CalendarEvent]:
        called["fetch"] += 1
        return []

    monkeypatch.setattr(mod, "fetch_google_today", _fetch)
    events = await mod.fetch_todays_events(fake_user, db)
    assert called["fetch"] == 0
    assert events == []
