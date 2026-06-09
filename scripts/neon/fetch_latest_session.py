"""Return the most recently STARTED conversation_sessions row, or None if the table is empty."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.neon.db_conn import DBConn


async def fetch_latest_session(db: DBConn) -> dict[str, Any] | None:
    row = await db.fetchrow(
        """SELECT id, user_id, persona_id, started_at, ended_at, duration_seconds
           FROM conversation_sessions
           ORDER BY started_at DESC
           LIMIT 1"""
    )
    return dict(row) if row else None
