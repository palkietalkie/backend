import uuid
from datetime import UTC, datetime

from app.notifications.notification_kinds import STREAK_WARNING
from app.notifications.streak_warning.find_streak_warning_candidates import (
    find_streak_warning_candidates,
)
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo: 12:00 UTC == 21:00 local == the streak-warning hour.
_STREAK_WARNING = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)
_DAILY_HOUR = datetime(
    2026, 6, 24, 10, 0, tzinfo=UTC
)  # Tokyo 19:00, the daily reminder hour, not the streak-warning hour


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        f"tok-{uuid.uuid4().hex[:8]}",
    )


async def test_streak_warning_hour_with_token_is_a_candidate(
    db: DBConn, fake_user: UserRow
) -> None:
    await _add_token(db, fake_user["id"])
    candidates = await find_streak_warning_candidates(db, _STREAK_WARNING)
    assert [c.user_id for c in candidates] == [fake_user["id"]]


async def test_daily_reminder_hour_is_not_the_streak_warning_hour(
    db: DBConn, fake_user: UserRow
) -> None:
    await _add_token(db, fake_user["id"])
    assert await find_streak_warning_candidates(db, _DAILY_HOUR) == []


async def test_already_streak_warning_reminded_today_is_excluded(
    db: DBConn, fake_user: UserRow
) -> None:
    await _add_token(db, fake_user["id"])
    await db.execute(
        """INSERT INTO notification_log (user_id, kind, per_kind_key)
           VALUES ($1, $2, ($3 AT TIME ZONE 'Asia/Tokyo')::date::text)""",
        fake_user["id"],
        STREAK_WARNING,
        _STREAK_WARNING,
    )
    assert await find_streak_warning_candidates(db, _STREAK_WARNING) == []
