import uuid

from app.services.neon.db_conn import DBConn


async def fetch_session_transcript(session_id: uuid.UUID, db: DBConn) -> list[tuple[str, str]]:
    """Both-speaker transcript for one session, in order — the raw material for the post-session summary (vs `fetch_session_user_turns`, which is user-only for word/phrase stats)."""
    rows = await db.fetch(
        "SELECT speaker, text FROM transcripts WHERE session_id = $1 ORDER BY started_at",
        session_id,
    )
    return [(row["speaker"], row["text"]) for row in rows]
