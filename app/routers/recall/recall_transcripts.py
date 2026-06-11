"""GET /recall/transcripts — Neon full-text search, called when the realtime model invokes the search_transcripts tool mid-conversation. Authenticated boundary (iOS can't reach Neon directly); thin by design (logic in search_transcripts). Best-effort: a dead dependency returns empty, never an error, so a tool call can't stall the live conversation."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.neon.search_transcripts import search_transcripts

router = APIRouter(prefix="/recall", tags=["recall"])
logger = logging.getLogger(__name__)


@router.get("/transcripts")
async def recall_transcripts(
    q: str = Query(..., min_length=1, max_length=200),
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> dict[str, Any]:
    try:
        return {"turns": await search_transcripts(user["id"], q, db)}
    except Exception:
        logger.exception("recall_transcripts failed for q=%r", q)
        return {"turns": []}
