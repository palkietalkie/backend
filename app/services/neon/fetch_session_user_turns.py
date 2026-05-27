import uuid

from app.services.neon.db_conn import DBConn


async def fetch_session_user_turns(session_id: uuid.UUID, db: DBConn) -> list[str]:
    rows = await db.fetch(
        "SELECT text FROM transcripts WHERE session_id = $1 AND speaker = 'user'",
        session_id,
    )
    return [row["text"] for row in rows]
