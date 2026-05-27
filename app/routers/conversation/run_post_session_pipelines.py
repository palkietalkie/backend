import contextlib
import uuid

from app.pipelines.kg_extraction.run_kg_extraction import run_kg_extraction
from app.pipelines.mistake_detection.run_mistake_detection import run_mistake_detection
from app.pipelines.phrase_extraction.run_phrase_extraction import run_phrase_extraction
from app.pipelines.transcript_analysis.run_transcript_analysis import run_transcript_analysis
from app.services.neon.get_pool import get_pool


async def run_post_session_pipelines(session_id: uuid.UUID, user_id: uuid.UUID) -> None:
    # Each pipeline catches its own exceptions internally; contextlib.suppress ensures one failing pipeline doesn't stop the rest.
    pool = await get_pool()
    async with pool.acquire() as db:
        with contextlib.suppress(Exception):
            await run_transcript_analysis(session_id, user_id, db)
        with contextlib.suppress(Exception):
            await run_phrase_extraction(session_id, user_id, db)
        with contextlib.suppress(Exception):
            await run_mistake_detection(session_id, user_id, db)
        with contextlib.suppress(Exception):
            await run_kg_extraction(session_id, user_id, db)
