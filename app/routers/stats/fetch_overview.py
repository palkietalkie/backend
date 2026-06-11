from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.cefr_vocab.constants import LEVELS as CEFR_LEVELS
from app.services.cefr_vocab.count_by_level import count_by_level
from app.services.cefr_vocab.count_used_by_level import count_used_by_level
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.list_user_lemmas import list_user_lemmas
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/stats", tags=["stats"])


class CefrCoverage(BaseModel):
    level: str
    total_words: int
    used_words: int
    coverage_pct: float


class StatsOverview(BaseModel):
    # Consecutive UTC-day streak ending today (or yesterday if no session today yet — the streak survives one "empty" day so it doesn't reset mid-afternoon before the user has practiced). 0 if no sessions in last 2 days.
    day_streak: int
    session_total_seconds: int
    sessions_count: int
    unique_words: int
    unique_phrases: int
    # null when no transcript yet (no sessions).
    user_talk_pct: float | None
    # null until at least 1s of user-talk time accumulates.
    speaking_rate_wpm: float | None
    # null until on-device pitch detection ships.
    pitch_range_hz: float | None
    cefr_coverage: list[CefrCoverage]


@router.get("", response_model=StatsOverview)
async def fetch_overview(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> StatsOverview:
    total_seconds = await db.fetchval(
        """SELECT COALESCE(SUM(duration_seconds), 0)::bigint
           FROM conversation_sessions
           WHERE user_id = $1""",
        user["id"],
    )

    session_days_rows = await db.fetch(
        """SELECT DISTINCT (started_at AT TIME ZONE 'UTC')::date AS day
           FROM conversation_sessions
           WHERE user_id = $1""",
        user["id"],
    )
    session_days = {row["day"] for row in session_days_rows}
    today_utc = datetime.now(UTC).date()
    cursor = today_utc if today_utc in session_days else today_utc - timedelta(days=1)
    day_streak = 0
    while cursor in session_days:
        day_streak += 1
        cursor -= timedelta(days=1)
    sessions_count = await db.fetchval(
        "SELECT COUNT(id)::bigint FROM conversation_sessions WHERE user_id = $1",
        user["id"],
    )
    unique_words = await db.fetchval(
        "SELECT COUNT(lemma)::bigint FROM word_freq WHERE user_id = $1",
        user["id"],
    )
    unique_phrases = await db.fetchval(
        "SELECT COUNT(phrase)::bigint FROM phrase_freq WHERE user_id = $1",
        user["id"],
    )

    # Text-derived audio approximations. Real audio analysis (per-chunk timing, pitch FFT) lives in a separate pipeline (TODO); these proxies give the user useful numbers immediately from data we already have.
    transcript_rows = await db.fetch(
        """SELECT t.speaker, t.text
           FROM transcripts t
           JOIN conversation_sessions s ON s.id = t.session_id
           WHERE s.user_id = $1""",
        user["id"],
    )
    user_chars = sum(len(row["text"]) for row in transcript_rows if row["speaker"] == "user")
    total_chars = sum(len(row["text"]) for row in transcript_rows)
    user_talk_pct: float | None = round(user_chars / total_chars, 3) if total_chars else None
    user_words = sum(
        len(row["text"].split()) for row in transcript_rows if row["speaker"] == "user"
    )
    user_talk_seconds = int(total_seconds or 0) * user_talk_pct if user_talk_pct else 0.0
    speaking_rate_wpm: float | None = (
        round(user_words / (user_talk_seconds / 60.0), 1) if user_talk_seconds >= 1 else None
    )

    pitch_row = await db.fetchrow(
        """SELECT MIN((props->>'min_hz')::float) AS pmin, MAX((props->>'max_hz')::float) AS pmax
           FROM events
           WHERE user_id = $1 AND event_type = 'pitch_range'""",
        user["id"],
    )
    pitch_range_hz: float | None = None
    if pitch_row is not None and pitch_row["pmin"] is not None and pitch_row["pmax"] is not None:
        pitch_range_hz = round(float(pitch_row["pmax"]) - float(pitch_row["pmin"]), 1)

    used_lemmas = await list_user_lemmas(db, user["id"])
    totals = count_by_level()
    used = count_used_by_level(used_lemmas)
    coverage = [
        CefrCoverage(
            level=level,
            total_words=totals[level],
            used_words=used[level],
            coverage_pct=round((used[level] / totals[level] * 100.0) if totals[level] else 0.0, 1),
        )
        for level in CEFR_LEVELS
    ]

    return StatsOverview(
        day_streak=day_streak,
        session_total_seconds=int(total_seconds or 0),
        sessions_count=int(sessions_count or 0),
        unique_words=int(unique_words or 0),
        unique_phrases=int(unique_phrases or 0),
        user_talk_pct=user_talk_pct,
        speaking_rate_wpm=speaking_rate_wpm,
        pitch_range_hz=pitch_range_hz,
        cefr_coverage=coverage,
    )
