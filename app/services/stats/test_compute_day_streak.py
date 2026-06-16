import uuid
from datetime import UTC, datetime, timedelta

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.stats.compute_day_streak import compute_day_streak


async def _session_on(db: DBConn, user_id: uuid.UUID, day: datetime) -> None:
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, $3, 60)""",
        uuid.uuid4(),
        user_id,
        day,
    )


async def test_zero_when_no_sessions(db: DBConn, fake_user: UserRow) -> None:
    assert await compute_day_streak(db, fake_user["id"]) == 0


async def test_counts_consecutive_days_then_stops_at_gap(db: DBConn, fake_user: UserRow) -> None:
    today = datetime.now(UTC)
    for delta in (0, 1, 2, 5):  # today + 2 back, gap, then one more
        await _session_on(db, fake_user["id"], today - timedelta(days=delta))
    assert await compute_day_streak(db, fake_user["id"]) == 3


async def test_streak_survives_no_session_today(db: DBConn, fake_user: UserRow) -> None:
    today = datetime.now(UTC)
    for delta in (1, 2):  # nothing today, but yesterday + day before
        await _session_on(db, fake_user["id"], today - timedelta(days=delta))
    assert await compute_day_streak(db, fake_user["id"]) == 2
