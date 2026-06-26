import uuid
from datetime import UTC, datetime

from app.notifications.find_weekly_recap_candidates import find_weekly_recap_candidates
from app.notifications.notification_kinds import WEEKLY_RECAP
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo. 2026-06-28 is a Sunday; Tokyo 18:00 == 09:00 UTC == the recap moment. Its ISO week is 2026-W26.
_RECAP = datetime(2026, 6, 28, 9, 0, tzinfo=UTC)
_WRONG_HOUR = datetime(2026, 6, 28, 10, 0, tzinfo=UTC)  # Sunday but Tokyo 19:00
_NOT_SUNDAY = datetime(2026, 6, 27, 9, 0, tzinfo=UTC)  # Tokyo Saturday 18:00
_ISO_WEEK = "2026-W26"


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        f"tok-{uuid.uuid4().hex[:8]}",
    )


async def test_sunday_recap_hour_with_token_is_a_candidate(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    candidates = await find_weekly_recap_candidates(db, _RECAP)
    assert [c.user_id for c in candidates] == [fake_user["id"]]
    assert candidates[0].iso_week == _ISO_WEEK


async def test_wrong_hour_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    assert await find_weekly_recap_candidates(db, _WRONG_HOUR) == []


async def test_non_sunday_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    assert await find_weekly_recap_candidates(db, _NOT_SUNDAY) == []


async def test_user_without_a_token_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    assert await find_weekly_recap_candidates(db, _RECAP) == []


async def test_already_recapped_this_week_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    await db.execute(
        "INSERT INTO notification_log (user_id, kind, per_kind_key) VALUES ($1, $2, $3)",
        fake_user["id"],
        WEEKLY_RECAP,
        _ISO_WEEK,
    )
    assert await find_weekly_recap_candidates(db, _RECAP) == []
