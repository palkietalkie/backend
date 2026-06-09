import logging
import uuid

from app.pipelines.kg_extraction.run_kg_extraction import run_kg_extraction
from app.pipelines.mistake_detection.run_mistake_detection import run_mistake_detection
from app.pipelines.phrase_extraction.run_phrase_extraction import run_phrase_extraction
from app.pipelines.transcript_analysis.run_transcript_analysis import run_transcript_analysis
from app.services.neon.get_pool import get_pool

_logger = logging.getLogger(__name__)


async def _run_one(name: str, coro: object) -> None:
    # One pipeline failing must not stop the rest, but silent swallow hides why word_freq / phrase_freq / mistakes / KG never populate. Log the exception with stack so Fly logs surface it.
    try:
        await coro  # type: ignore[misc]
    except Exception:
        _logger.exception("post-session pipeline %s failed", name)


async def run_post_session_pipelines(session_id: uuid.UUID, user_id: uuid.UUID) -> None:
    pool = await get_pool()
    async with pool.acquire() as db:
        await _run_one("transcript_analysis", run_transcript_analysis(session_id, user_id, db))
        await _run_one("phrase_extraction", run_phrase_extraction(session_id, user_id, db))
        await _run_one("mistake_detection", run_mistake_detection(session_id, user_id, db))
        await _run_one("kg_extraction", run_kg_extraction(session_id, user_id, db))
