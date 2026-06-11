import uuid

from app.services.neon.db_conn import DBConn


async def search_transcripts(
    user_id: uuid.UUID, query: str, db: DBConn, limit: int = 5
) -> list[dict[str, str]]:
    """Keyword (full-text) search over the user's past transcript turns. Backs the conversation-time keyword-recall tool — the model calls this when it needs the user's own past words verbatim (exact name, phrase, decision), where semantic similarity isn't precise enough."""
    rows = await db.fetch(
        """SELECT t.speaker, t.text, s.started_at
           FROM transcripts t
           JOIN conversation_sessions s ON s.id = t.session_id
           WHERE s.user_id = $1
             -- Full-text match, not LIKE: to_tsvector stems t.text into stop-word-free lexemes, e.g. "I was running" -> 'run'.
             -- plainto_tsquery stems the raw query $2 the same way and ANDs the terms, e.g. "running shoes" -> 'run' & 'shoe'.
             -- @@ matches when every query lexeme is present, so "run" finds "running"/"ran".
             AND to_tsvector('english', t.text) @@ plainto_tsquery('english', $2)
           ORDER BY s.started_at DESC
           LIMIT $3""",
        user_id,
        query,
        limit,
    )
    return [
        {"speaker": r["speaker"], "text": r["text"], "when": r["started_at"].isoformat()}
        for r in rows
    ]
