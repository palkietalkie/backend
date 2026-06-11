"""GET /recall/conversations — Pinecone semantic recall, called when the realtime model invokes the recall_past_conversations tool mid-conversation. Authenticated boundary (iOS can't reach Pinecone directly); thin by design (logic in query_transcript_memory). Best-effort: a dead dependency returns empty, never an error, so a tool call can't stall the live conversation."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.rows import UserRow
from app.services.pinecone.query_transcript_memory import query_transcript_memory

router = APIRouter(prefix="/recall", tags=["recall"])
logger = logging.getLogger(__name__)


@router.get("/conversations")
async def recall_conversations(
    q: str = Query(..., min_length=1, max_length=200),
    user: UserRow = Depends(resolve_current_user),
) -> dict[str, Any]:
    try:
        return {"snippets": await query_transcript_memory(user["id"], q)}
    except Exception:
        logger.exception("recall_conversations failed for q=%r", q)
        return {"snippets": []}
