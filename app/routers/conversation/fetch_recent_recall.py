import uuid

from app.services.fallback import fallback
from app.services.neon.db_conn import DBConn


@fallback(default=None)
async def fetch_recent_recall(
    user_id: uuid.UUID, persona_id: uuid.UUID, target_language: str, db: DBConn
) -> str | None:
    """Tail of the user's last 3 finished conversations WITH THIS PERSONA in the SAME target language, for prompt recall.

    Each persona keeps its own memory of the user — Aiden isn't fed Naoko's transcript tail. Three sessions (not one) so the persona has shared history beyond the very last chat; longer-term recall (per-session summaries + vector search) is the planned upgrade in /CLAUDE.md. Returns None when there's nothing to recall.

    Same-language only: feeding a Japanese session's transcript into an English session pulls the tutor back into Japanese (the prompt tells it to pick up unfinished threads). Pre-fix rows have a NULL target_language — excluded rather than guessed, so the worst case is a missed callback, never a wrong-language opening.
    """
    last_rows = await db.fetch(
        """SELECT id, started_at, ended_at
           FROM conversation_sessions
           WHERE user_id = $1 AND persona_id = $2 AND ended_at IS NOT NULL
                 AND target_language = $3
           ORDER BY ended_at DESC
           LIMIT 3""",
        user_id,
        persona_id,
        target_language,
    )
    if not last_rows:
        return None
    session_tails: list[str] = []
    for session_row in reversed(last_rows):
        transcript_rows = await db.fetch(
            """SELECT speaker, text
               FROM transcripts
               WHERE session_id = $1
               ORDER BY started_at DESC
               LIMIT 10""",
            session_row["id"],
        )
        if not transcript_rows:
            continue
        ordered = list(reversed(transcript_rows))
        session_tails.append(" | ".join(f"{t['speaker']}: {t['text'][:200]}" for t in ordered))
    return "\n---\n".join(session_tails) if session_tails else None
