import uuid
from datetime import UTC, datetime

from app.notifications.find_daily_content_candidates import find_daily_content_candidates
from app.notifications.notification_kinds import DAILY_CONTENT
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo. Tokyo 07:00 == 22:00 UTC the previous day == the content-nudge hour.
_MORNING = datetime(2026, 6, 23, 22, 0, tzinfo=UTC)
_WRONG_HOUR = datetime(2026, 6, 23, 23, 0, tzinfo=UTC)  # Tokyo 08:00
_LOCAL_TODAY = "2026-06-24"


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        f"tok-{uuid.uuid4().hex[:8]}",
    )


async def test_morning_hour_with_token_is_a_candidate(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    candidates = await find_daily_content_candidates(db, _MORNING)
    assert [c.user_id for c in candidates] == [fake_user["id"]]
    assert candidates[0].local_today == _LOCAL_TODAY


async def test_wrong_hour_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    assert await find_daily_content_candidates(db, _WRONG_HOUR) == []


async def test_user_without_a_token_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    assert await find_daily_content_candidates(db, _MORNING) == []


async def test_already_nudged_today_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    await db.execute(
        "INSERT INTO notification_log (user_id, kind, per_kind_key) VALUES ($1, $2, $3)",
        fake_user["id"],
        DAILY_CONTENT,
        _LOCAL_TODAY,
    )
    assert await find_daily_content_candidates(db, _MORNING) == []
