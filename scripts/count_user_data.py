import asyncpg


async def count_user_data(conn: asyncpg.Connection, user_id: str) -> dict[str, int]:
    """Per-table row counts for one user — the before/after readout the merge prints so the move is auditable."""
    return {
        "sessions": await conn.fetchval(
            "SELECT count(*) FROM conversation_sessions WHERE user_id=$1", user_id
        ),
        "transcripts": await conn.fetchval(
            "SELECT count(*) FROM transcripts t JOIN conversation_sessions s ON s.id=t.session_id WHERE s.user_id=$1",
            user_id,
        ),
        "events": await conn.fetchval("SELECT count(*) FROM events WHERE user_id=$1", user_id),
        "word_freq": await conn.fetchval(
            "SELECT count(*) FROM word_freq WHERE user_id=$1", user_id
        ),
        "phrase_freq": await conn.fetchval(
            "SELECT count(*) FROM phrase_freq WHERE user_id=$1", user_id
        ),
        "mistakes": await conn.fetchval("SELECT count(*) FROM mistakes WHERE user_id=$1", user_id),
        "personas": await conn.fetchval("SELECT count(*) FROM personas WHERE user_id=$1", user_id),
        "session_audio": await conn.fetchval(
            "SELECT count(*) FROM session_audio WHERE user_id=$1", user_id
        ),
    }
