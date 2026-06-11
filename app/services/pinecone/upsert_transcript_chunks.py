import asyncio
import uuid

from app.services.pinecone.get_memory_index import get_memory_index


async def upsert_transcript_chunks(
    user_id: uuid.UUID, session_id: uuid.UUID, chunks: list[str]
) -> None:
    """Embed + store a session's transcript chunks for semantic recall, namespaced by user so recall only ever sees their own sessions. The Pinecone SDK is synchronous, so the call runs in a worker thread to keep the event loop free."""
    if not chunks:
        return
    index = get_memory_index()
    # `text` is the field the index embeds (see get_memory_index field_map); Pinecone embeds it server-side. One record per chunk so a long session isn't truncated into a single vector.
    records = [
        {"_id": f"{session_id}:{i}", "text": chunk, "session_id": str(session_id)}
        for i, chunk in enumerate(chunks)
    ]
    await asyncio.to_thread(index.upsert_records, namespace=str(user_id), records=records)
