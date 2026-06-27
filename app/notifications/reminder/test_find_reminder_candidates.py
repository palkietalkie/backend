import uuid
from datetime import UTC, datetime

from app.notifications.notification_kinds import DAILY_REMINDER
from app.notifications.reminder.find_reminder_candidates import find_reminder_candidates
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo (UTC+9), so 10:00 UTC == 19:00 local == the default reminder hour.
_DUE = datetime(2026, 6, 24, 10, 0, tzinfo=UTC)
_NOT_DUE = datetime(2026, 6, 24, 0, 0, tzinfo=UTC)  # local 09:00, not 19


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        f"tok-{uuid.uuid4().hex[:8]}",
    )


async def test_due_user_with_token_is_a_candidate(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    candidates = await find_reminder_candidates(db, _DUE)
    assert [c.user_id for c in candidates] == [fake_user["id"]]


async def test_user_off_their_reminder_hour_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    assert await find_reminder_candidates(db, _NOT_DUE) == []


async def test_user_without_a_token_is_excluded(db: DBConn, fake_user: UserRow) -> None:
    # No device token → nowhere to deliver → not a candidate even at the right hour.
    assert await find_reminder_candidates(db, _DUE) == []


async def test_reminders_disabled_excludes_the_user(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    await db.execute(
        "INSERT INTO notification_prefs (user_id, reminders_enabled) VALUES ($1, FALSE)",
        fake_user["id"],
    )
    assert await find_reminder_candidates(db, _DUE) == []


async def test_already_reminded_today_excludes_the_user(db: DBConn, fake_user: UserRow) -> None:
    await _add_token(db, fake_user["id"])
    await db.execute(
        """INSERT INTO notification_log (user_id, kind, per_kind_key)
           VALUES ($1, $2, ($3 AT TIME ZONE 'Asia/Tokyo')::date::text)""",
        fake_user["id"],
        DAILY_REMINDER,
        _DUE,
    )
    assert await find_reminder_candidates(db, _DUE) == []
