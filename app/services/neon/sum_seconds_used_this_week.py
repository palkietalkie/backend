from app.routers.entitlement.compute_local_week_window import compute_local_week_window
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def sum_seconds_used_this_week(user: UserRow, db: DBConn) -> int:
    start_utc, end_utc = compute_local_week_window(user["timezone"])
    value = await db.fetchval(
        """SELECT COALESCE(SUM(duration_seconds), 0)::bigint
           FROM conversation_sessions
           WHERE user_id = $1
             AND started_at >= $2
             AND started_at <  $3
             AND duration_seconds IS NOT NULL""",
        user["id"],
        start_utc,
        end_utc,
    )
    return int(value) if value is not None else 0
