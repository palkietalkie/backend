"""Tests for GET /entitlement — surfaces remaining-minutes math + the published caps inline.

The router-shape test_entitlement_router.py already covers most cases; this file pins the cap fields and the week-window remaining-minutes math separately so a future split keeps both anchors."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_entitlement_returns_both_caps_inline(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/entitlement")
    assert resp.status_code == 200
    body = resp.json()
    # iOS reads caps off the entitlement response so the SubscriptionView copy stays in lockstep.
    assert body["free_minutes_per_day_cap"] == FREE_MINUTES_PER_DAY
    assert body["free_minutes_per_week_cap"] == FREE_MINUTES_PER_WEEK


async def test_entitlement_consumed_minutes_reduce_week_budget(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    # A session earlier this week (not today) so the week budget drops but today doesn't.
    started = datetime.now(UTC) - timedelta(hours=1)
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, $3, 300)""",
        uuid.uuid4(),
        user["id"],
        started,
    )
    body = (await client.get("/entitlement")).json()
    # 5 min consumed → 5 fewer minutes left this week than the cap.
    assert body["free_minutes_remaining_this_week"] == FREE_MINUTES_PER_WEEK - 5


async def test_entitlement_clamps_remaining_to_zero(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # Burn the full week cap; remaining must not go negative.
    client, user = app_with_overrides
    over_seconds = (FREE_MINUTES_PER_WEEK + 5) * 60
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), $3)""",
        uuid.uuid4(),
        user["id"],
        over_seconds,
    )
    body = (await client.get("/entitlement")).json()
    assert body["free_minutes_remaining_this_week"] == 0
    assert body["free_minutes_remaining_today"] == 0


async def test_entitlement_premium_user_skips_db_count(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await db.execute("UPDATE users SET premium = TRUE WHERE id = $1", user["id"])
    body = (await client.get("/entitlement")).json()
    assert body["is_premium"] is True
    # Premium always reports the full cap regardless of usage.
    assert body["free_minutes_remaining_today"] == FREE_MINUTES_PER_DAY
    assert body["free_minutes_remaining_this_week"] == FREE_MINUTES_PER_WEEK
