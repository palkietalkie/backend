"""Return every transcript row for a given session, ordered chronologically."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.neon.db_conn import DBConn


async def fetch_session_transcripts(db: DBConn, session_id: uuid.UUID) -> list[dict[str, Any]]:
    rows = await db.fetch(
        """SELECT speaker, started_at, text
           FROM transcripts
           WHERE session_id = $1
           ORDER BY started_at ASC""",
        session_id,
    )
    return [dict(r) for r in rows]
