"""Tests for google_calendar.refresh_token — Google token endpoint mocked via respx."""

import uuid
from datetime import UTC, datetime

import httpx
import respx

from app.services.google_calendar.refresh_token import TOKEN_URL, refresh_token
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import CalendarTokenRow


async def _seed(db: DBConn, *, with_refresh: bool = True) -> CalendarTokenRow:
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    token_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token)
           VALUES ($1, $2, 'google', 'old', $3)""",
        token_id,
        user_id,
        "rt-x" if with_refresh else None,
    )
    now = datetime.now(UTC)
    return CalendarTokenRow(
        id=token_id,
        user_id=user_id,
        provider="google",
        access_token="old",
        refresh_token="rt-x" if with_refresh else None,
        expires_at=None,
        created_at=now,
        updated_at=now,
    )


@respx.mock
async def test_refresh_token_updates_in_place(db: DBConn) -> None:
    respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(200, json={"access_token": "new-at", "expires_in": 3600})
    )
    token = await _seed(db)
    await refresh_token(token, db)
    assert token["access_token"] == "new-at"
    row = await db.fetchrow(
        "SELECT access_token, expires_at FROM calendar_tokens WHERE id = $1", token["id"]
    )
    assert row is not None
    assert row["access_token"] == "new-at"
    assert row["expires_at"] is not None


@respx.mock
async def test_refresh_token_no_op_without_refresh_token(db: DBConn) -> None:
    token = await _seed(db, with_refresh=False)
    # Setup a route that should NOT be called.
    route = respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={}))
    await refresh_token(token, db)
    assert not route.called
    assert token["access_token"] == "old"


@respx.mock
async def test_refresh_token_handles_missing_expires_in(db: DBConn) -> None:
    respx.post(TOKEN_URL).mock(return_value=httpx.Response(200, json={"access_token": "new-at"}))
    token = await _seed(db)
    await refresh_token(token, db)
    assert token["expires_at"] is None
