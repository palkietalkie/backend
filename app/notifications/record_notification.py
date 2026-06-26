import uuid

from app.services.neon.db_conn import DBConn


async def record_notification(db: DBConn, user_id: uuid.UUID, kind: str, per_kind_key: str) -> None:
    """Stamp a sent notification in notification_log so the same (user, kind, per_kind_key) won't fire again.

    Idempotent: a scheduler restart that re-runs a tick, or two concurrent ticks, hit the primary key and no-op instead of double-sending."""
    await db.execute(
        """INSERT INTO notification_log (user_id, kind, per_kind_key)
           VALUES ($1, $2, $3)
           ON CONFLICT (user_id, kind, per_kind_key) DO NOTHING""",
        user_id,
        kind,
        per_kind_key,
    )
