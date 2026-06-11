import logging
import uuid

from app.pipelines.transcript_embedding.chunk_transcript import chunk_transcript
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_session_transcript import fetch_session_transcript
from app.services.pinecone.upsert_transcript_chunks import upsert_transcript_chunks

_logger = logging.getLogger(__name__)


async def run_transcript_embedding(session_id: uuid.UUID, user_id: uuid.UUID, db: DBConn) -> int:
    """Chunk the finished session's transcript and embed the chunks into Pinecone for semantic recall. Returns the chunk count. No LLM summary — the transcript itself is the recall source (keyword search covers exact recall; this covers by-meaning)."""
    turns = await fetch_session_transcript(session_id, db)
    chunks = chunk_transcript(turns)
    if not chunks:
        return 0
    try:
        await upsert_transcript_chunks(user_id, session_id, chunks)
    except Exception:
        # Pinecone is best-effort; chunks are re-derivable from transcripts on a later run. Log so it's visible in Fly logs rather than silently dropping recall data.
        _logger.exception("pinecone transcript upsert failed for session %s", session_id)
        return 0
    return len(chunks)
