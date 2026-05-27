from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.apple_asn.apply_decision import apply_decision
from app.services.neon.db_conn import DBConn


async def test_apply_decision_active(db: DBConn, apple_user: dict[str, Any]) -> None:
    expires_at = datetime.now(UTC) + timedelta(days=30)
    await apply_decision(
        db,
        clerk_user_id=apple_user["clerk_user_id"],
        decision=("active", False),
        expires_at=expires_at,
        auto_renew=1,
    )
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", apple_user["id"]
    )
    assert row is not None
    assert row["premium"] is True
    # auto_renew=1, cancel_at_period_end=False → premium_ends_at cleared
    assert row["premium_ends_at"] is None


async def test_apply_decision_revoke_immediately(db: DBConn, apple_user: dict[str, Any]) -> None:
    await db.execute("UPDATE users SET premium = TRUE WHERE id = $1", apple_user["id"])
    await apply_decision(
        db,
        clerk_user_id=apple_user["clerk_user_id"],
        decision=("revoke", False),
        expires_at=None,
        auto_renew=0,
    )
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", apple_user["id"]
    )
    assert row is not None
    assert row["premium"] is False
    assert row["premium_ends_at"] is not None


async def test_apply_decision_cancel_at_period_end(db: DBConn, apple_user: dict[str, Any]) -> None:
    expires_at = datetime.now(UTC) + timedelta(days=10)
    await apply_decision(
        db,
        clerk_user_id=apple_user["clerk_user_id"],
        decision=("active", True),
        expires_at=expires_at,
        auto_renew=0,
    )
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", apple_user["id"]
    )
    assert row is not None
    assert row["premium"] is True
    assert row["premium_ends_at"] is not None
