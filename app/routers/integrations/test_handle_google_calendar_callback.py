"""Tests for the OAuth callback that exchanges Google's authorization code for tokens and persists them.

The token exchange POST to oauth2.googleapis.com is mocked with respx so the test never makes a real network call."""

import uuid
from datetime import UTC, datetime, timedelta

import httpx
import respx
from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


@respx.mock
async def test_callback_inserts_new_token_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(
            200, json={"access_token": "at-fresh", "refresh_token": "rt-fresh", "expires_in": 3600}
        )
    )
    client, user = app_with_overrides
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "auth-code", "state": user["clerk_user_id"]},
        follow_redirects=False,
    )
    assert resp.status_code == 307
    assert resp.headers["location"] == "palkietalkie://integrations/google-calendar/connected"
    row = await db.fetchrow(
        "SELECT access_token, refresh_token, expires_at FROM calendar_tokens WHERE user_id = $1",
        user["id"],
    )
    assert row is not None
    assert row["access_token"] == "at-fresh"
    assert row["refresh_token"] == "rt-fresh"
    # expires_at must be ~1h in the future (within a few-second slack for test runtime).
    assert row["expires_at"] is not None
    delta = row["expires_at"] - datetime.now(UTC)
    assert timedelta(minutes=55) < delta < timedelta(minutes=65)


@respx.mock
async def test_callback_upserts_existing_token_keeping_refresh(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # Google omits the refresh_token on subsequent OAuth completions; we must NOT clobber the original.
    client, user = app_with_overrides
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, 'google', 'old-at', 'original-rt', $3)""",
        uuid.uuid4(),
        user["id"],
        datetime.now(UTC),
    )
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "rotated-at", "expires_in": 1800})
    )
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "code", "state": user["clerk_user_id"]},
        follow_redirects=False,
    )
    assert resp.status_code == 307
    row = await db.fetchrow(
        "SELECT access_token, refresh_token FROM calendar_tokens WHERE user_id = $1",
        user["id"],
    )
    assert row is not None
    assert row["access_token"] == "rotated-at"
    # The original refresh_token must survive.
    assert row["refresh_token"] == "original-rt"


@respx.mock
async def test_callback_400_for_unknown_clerk_state(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "at"})
    )
    client, _ = app_with_overrides
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "code", "state": "nobody"},
        follow_redirects=False,
    )
    assert resp.status_code == 400


@respx.mock
async def test_callback_expires_at_null_when_no_expires_in(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    respx.post("https://oauth2.googleapis.com/token").mock(
        return_value=httpx.Response(200, json={"access_token": "at-no-exp"})
    )
    client, user = app_with_overrides
    resp = await client.get(
        "/integrations/google-calendar/callback",
        params={"code": "code", "state": user["clerk_user_id"]},
        follow_redirects=False,
    )
    assert resp.status_code == 307
    expires_at = await db.fetchval(
        "SELECT expires_at FROM calendar_tokens WHERE user_id = $1", user["id"]
    )
    assert expires_at is None
