"""Tests for /integrations endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_list_integrations_starts_empty(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/integrations")
    assert resp.status_code == 200
    body = resp.json()
    providers = {row["provider"]: row for row in body}
    assert providers["google"]["connected"] is False
    assert providers["apple"]["connected"] is False
    assert providers["outlook"]["connected"] is False


async def test_list_integrations_reflects_token_state(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    expires = datetime.now(UTC) + timedelta(hours=1)
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, 'google', 'at', 'rt', $3)""",
        uuid.uuid4(),
        user["id"],
        expires,
    )
    resp = await client.get("/integrations")
    providers = {row["provider"]: row for row in resp.json()}
    assert providers["google"]["connected"] is True


async def test_connect_google_calendar_returns_auth_url(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client")
    monkeypatch.setenv("GOOGLE_OAUTH_REDIRECT_URI", "http://localhost/callback")
    get_settings.cache_clear()
    try:
        client, user = app_with_overrides
        resp = await client.post("/integrations/google-calendar/connect")
        assert resp.status_code == 200
        url: str = resp.json()["auth_url"]
        parsed = urlparse(url)
        assert parsed.netloc == "accounts.google.com"
        qs = parse_qs(parsed.query)
        assert qs["state"] == [user["clerk_user_id"]]
        assert qs["client_id"] == ["test-client"]
    finally:
        get_settings.cache_clear()


async def test_connect_google_calendar_503_without_client_id(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "")
    get_settings.cache_clear()
    try:
        client, _ = app_with_overrides
        resp = await client.post("/integrations/google-calendar/connect")
        assert resp.status_code == 503
    finally:
        get_settings.cache_clear()


async def test_connect_outlook_returns_501(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post("/integrations/outlook/connect")
    assert resp.status_code == 501


async def test_push_apple_calendar_events_writes_event_rows(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    resp = await client.post(
        "/integrations/apple-calendar/events",
        json=[
            {
                "title": "Standup",
                "start": now.isoformat(),
                "end": (now + timedelta(minutes=15)).isoformat(),
                "location": "Zoom",
            }
        ],
    )
    assert resp.status_code == 204
    rows = await db.fetch(
        "SELECT props FROM events WHERE user_id = $1 AND event_type = 'apple_calendar_event'",
        user["id"],
    )
    assert len(rows) == 1
    assert rows[0]["props"]["title"] == "Standup"


@respx.mock
async def test_handle_google_calendar_callback_persists_token(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200,
            json={
                "access_token": "at-x",
                "refresh_token": "rt-x",
                "expires_in": 3600,
            },
        )
    )
    client, user = app_with_overrides
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "abc", "state": user["clerk_user_id"]},
        follow_redirects=False,
    )
    assert resp.status_code == 307
    assert resp.headers["location"].startswith("palkietalkie://")
    row = await db.fetchrow(
        "SELECT access_token, refresh_token FROM calendar_tokens WHERE user_id = $1",
        user["id"],
    )
    assert row is not None
    assert row["access_token"] == "at-x"
    assert row["refresh_token"] == "rt-x"


@respx.mock
async def test_handle_google_calendar_callback_400_for_unknown_state(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "at"})
    )
    client, _ = app_with_overrides
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "abc", "state": "unknown_user"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
