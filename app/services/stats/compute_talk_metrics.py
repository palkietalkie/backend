import uuid
from dataclasses import dataclass

from app.services.neon.db_conn import DBConn


@dataclass(frozen=True)
class TalkMetrics:
    # null when no transcript yet (no sessions).
    user_talk_pct: float | None
    # null until at least 1s of inferred user-talk time accumulates.
    speaking_rate_wpm: float | None


async def compute_talk_metrics(db: DBConn, user_id: uuid.UUID, total_seconds: int) -> TalkMetrics:
    """Transcript-derived approximations of talk share and speaking rate.

    These are text proxies: real audio analysis (per-chunk timing) is a separate pipeline. user_talk_pct is the character ratio between the user's turns and all turns; speaking_rate_wpm divides the user's word count by the inferred time they spent speaking (session duration scaled by talk share).
    """
    rows = await db.fetch(
        """SELECT t.speaker, t.text
           FROM transcripts t
           JOIN conversation_sessions s ON s.id = t.session_id
           WHERE s.user_id = $1""",
        user_id,
    )
    user_chars = sum(len(row["text"]) for row in rows if row["speaker"] == "user")
    total_chars = sum(len(row["text"]) for row in rows)
    talk_pct = round(user_chars / total_chars, 3) if total_chars else None
    user_words = sum(len(row["text"].split()) for row in rows if row["speaker"] == "user")
    user_talk_seconds = total_seconds * talk_pct if talk_pct else 0.0
    rate = round(user_words / (user_talk_seconds / 60.0), 1) if user_talk_seconds >= 1 else None
    return TalkMetrics(user_talk_pct=talk_pct, speaking_rate_wpm=rate)
