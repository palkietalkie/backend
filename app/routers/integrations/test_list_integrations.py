"""Tests for GET /integrations — provider connection status derived from calendar_tokens.

The route runs through the per-test transaction-bound connection injected by app_with_overrides, so DB seeds here are visible to the route and vice versa."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_returns_all_three_providers_disconnected_by_default(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/integrations")
    assert resp.status_code == 200
    body = resp.json()
    # The route always emits exactly google / apple / outlook, in that order.
    assert [row["provider"] for row in body] == ["google", "apple", "outlook"]
    for row in body:
        assert row["connected"] is False
        assert row["expires_at"] is None


async def test_connected_true_and_expires_at_surfaced_for_seeded_token(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    expires = datetime.now(UTC) + timedelta(hours=2)
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, 'google', 'at', 'rt', $3)""",
        uuid.uuid4(),
        user["id"],
        expires,
    )
    resp = await client.get("/integrations")
    assert resp.status_code == 200
    providers = {row["provider"]: row for row in resp.json()}
    assert providers["google"]["connected"] is True
    # expires_at echoes the stored token expiry (to the second).
    returned = datetime.fromisoformat(providers["google"]["expires_at"])
    assert abs((returned - expires).total_seconds()) < 1
    # The other providers stay disconnected.
    assert providers["apple"]["connected"] is False
    assert providers["outlook"]["connected"] is False


async def test_only_own_tokens_count(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # A token belonging to a different user must NOT mark the current user connected.
    client, user = app_with_overrides
    other_user_id = uuid.uuid4()
    now = datetime.now(UTC)
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, email, preferred_name, native_languages,
                              location_city, timezone, created_at, updated_at)
           VALUES ($1, $2, $3, 'Other', $4, 'LA', 'America/Los_Angeles', $5, $5)""",
        other_user_id,
        f"user_{uuid.uuid4().hex[:12]}",
        "other@palkietalkie.test",
        ["Japanese"],
        now,
    )
    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, 'google', 'at', 'rt', $3)""",
        uuid.uuid4(),
        other_user_id,
        now + timedelta(hours=1),
    )
    resp = await client.get("/integrations")
    providers = {row["provider"]: row for row in resp.json()}
    assert providers["google"]["connected"] is False
    assert user["id"] != other_user_id
