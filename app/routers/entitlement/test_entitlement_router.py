"""Tests for entitlement: check_is_premium_now (pure) + GET /entitlement (router)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


def _user(*, premium: bool, ends_at: datetime | None = None) -> UserRow:
    now = datetime.now(UTC)
    return UserRow(
        id=uuid.uuid4(),
        clerk_user_id="u",
        email=None,
        premium=premium,
        premium_ends_at=ends_at,
        created_at=now,
        updated_at=now,
        preferred_name=None,
        name_pronunciation=None,
        native_languages=["English"],
        target_accents=[],
        target_language="English",
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=None,
        location_city=None,
        timezone=None,
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
        deleted_at=None,
    )


def test_check_is_premium_now_false_when_not_premium() -> None:
    assert check_is_premium_now(_user(premium=False)) is False


def test_check_is_premium_now_true_when_no_end_date() -> None:
    assert check_is_premium_now(_user(premium=True)) is True


def test_check_is_premium_now_true_when_end_in_future() -> None:
    assert (
        check_is_premium_now(_user(premium=True, ends_at=datetime.now(UTC) + timedelta(days=1)))
        is True
    )


def test_check_is_premium_now_false_when_end_in_past() -> None:
    assert (
        check_is_premium_now(_user(premium=True, ends_at=datetime.now(UTC) - timedelta(days=1)))
        is False
    )


def test_check_is_premium_now_handles_naive_datetime() -> None:
    # ``replace(tzinfo=None)`` simulates a row from a DB driver that strips tzinfo.
    naive = (datetime.now(UTC) + timedelta(days=1)).replace(tzinfo=None)
    assert check_is_premium_now(_user(premium=True, ends_at=naive)) is True


async def test_fetch_entitlement_free_user_full_budget(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/entitlement")
    assert resp.status_code == 200
    body = resp.json()
    assert body["is_premium"] is False
    assert body["free_minutes_remaining_today"] == 10


async def test_fetch_entitlement_consumed_minutes_reduce_budget(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    sid = uuid.uuid4()
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), 180)""",
        sid,
        user["id"],
    )
    resp = await client.get("/entitlement")
    body = resp.json()
    assert body["free_minutes_remaining_today"] == 7


async def test_fetch_entitlement_premium_returns_full_minutes(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await db.execute("UPDATE users SET premium = TRUE WHERE id = $1", user["id"])
    resp = await client.get("/entitlement")
    body = resp.json()
    assert body["is_premium"] is True
    assert body["free_minutes_remaining_today"] == 10
