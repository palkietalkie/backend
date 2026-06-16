import uuid
from datetime import UTC, datetime, timedelta

from app.services.neon.db_conn import DBConn


async def compute_day_streak(db: DBConn, user_id: uuid.UUID) -> int:
    """Consecutive UTC-day streak ending today, or yesterday if there's no session today yet.

    The grace day means the streak doesn't reset mid-afternoon before the user has had a chance to practice. 0 when there's no session in the last two days.
    """
    rows = await db.fetch(
        """SELECT DISTINCT (started_at AT TIME ZONE 'UTC')::date AS day
           FROM conversation_sessions
           WHERE user_id = $1""",
        user_id,
    )
    session_days = {row["day"] for row in rows}
    today = datetime.now(UTC).date()
    cursor = today if today in session_days else today - timedelta(days=1)
    streak = 0
    while cursor in session_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak
