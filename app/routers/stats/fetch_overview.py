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
from app.services.stats.compute_affinity import compute_affinity
from app.services.stats.compute_day_streak import compute_day_streak
from app.services.stats.compute_pitch_range import compute_pitch_range
from app.services.stats.compute_talk_metrics import compute_talk_metrics

router = APIRouter(prefix="/stats", tags=["stats"])


class CefrCoverage(BaseModel):
    level: str
    total_words: int
    used_words: int
    coverage_pct: float


class StatsOverview(BaseModel):
    day_streak: int
    session_total_seconds: int
    sessions_count: int
    unique_words: int
    unique_phrases: int
    user_talk_pct: float | None
    speaking_rate_wpm: float | None
    # The actual pitch endpoints (lowest and highest F0 across sessions), so the client shows a range like 90-230 Hz. Both null until on-device pitch detection has reported.
    pitch_min_hz: float | None
    pitch_max_hz: float | None
    # Affinity, normalized -100 to 100 (0 neutral): the tutor's reactions (laugh / cheer / gasp earn it, sigh / groan penalize it), detected live on-device, combined as a favorability ratio. See compute_affinity.
    affinity: int
    cefr_coverage: list[CefrCoverage]


@router.get("", response_model=StatsOverview)
async def fetch_overview(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> StatsOverview:
    user_id = user["id"]
    total_seconds = int(
        await db.fetchval(
            """SELECT COALESCE(SUM(duration_seconds), 0)::bigint
               FROM conversation_sessions
               WHERE user_id = $1""",
            user_id,
        )
        or 0
    )
    sessions_count = await db.fetchval(
        "SELECT COUNT(id)::bigint FROM conversation_sessions WHERE user_id = $1",
        user_id,
    )
    unique_words = await db.fetchval(
        "SELECT COUNT(lemma)::bigint FROM word_freq WHERE user_id = $1",
        user_id,
    )
    unique_phrases = await db.fetchval(
        "SELECT COUNT(phrase)::bigint FROM phrase_freq WHERE user_id = $1",
        user_id,
    )

    day_streak = await compute_day_streak(db, user_id)
    talk = await compute_talk_metrics(db, user_id, total_seconds)
    pitch = await compute_pitch_range(db, user_id)
    affinity = await compute_affinity(db, user_id)

    used_lemmas = await list_user_lemmas(db, user_id)
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
        session_total_seconds=total_seconds,
        sessions_count=int(sessions_count or 0),
        unique_words=int(unique_words or 0),
        unique_phrases=int(unique_phrases or 0),
        user_talk_pct=talk.user_talk_pct,
        speaking_rate_wpm=talk.speaking_rate_wpm,
        pitch_min_hz=pitch.min_hz,
        pitch_max_hz=pitch.max_hz,
        affinity=affinity,
        cefr_coverage=coverage,
    )
