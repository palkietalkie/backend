import asyncio
import uuid

from app.services.pinecone.get_memory_index import get_memory_index


async def query_transcript_memory(user_id: uuid.UUID, query: str, top_k: int = 3) -> list[str]:
    """Semantic recall: return the transcript chunks from the user's past sessions most relevant to `query`. Backs the conversation-time semantic-recall tool — the model calls it when the current topic echoes something from earlier sessions by meaning, even when the words differ ("I have a demo coming up" → past "scared of presentations" chat)."""
    index = get_memory_index()
    res = await asyncio.to_thread(
        index.search,
        namespace=str(user_id),
        query={"inputs": {"text": query}, "top_k": top_k},
    )
    hits = res.get("result", {}).get("hits", [])
    return [h.get("fields", {}).get("text", "") for h in hits if h.get("fields")]
