"""GET /recall/web_fetch — fetch a public URL's readable text, called when the realtime model invokes the web_fetch tool mid-conversation.

iOS receives the model's tool call over its direct iOS to OpenAI WebSocket and has no HTTP stack tuned for scraping, so the fetch happens server-side behind the Clerk-authenticated boundary. Thin by design (logic in fetch_url_text). Best-effort: a failure returns empty content, never an error, so a tool call can't stall the live conversation.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.resolve_current_user import resolve_current_user
from app.services.http.fetch_url_text import fetch_url_text
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/recall", tags=["recall"])
logger = logging.getLogger(__name__)


@router.get("/web_fetch")
async def web_fetch(
    url: str = Query(..., min_length=8, max_length=2000),
    _user: UserRow = Depends(resolve_current_user),
) -> dict[str, Any]:
    try:
        return {"content": await fetch_url_text(url)}
    except Exception:
        logger.exception("web_fetch failed for url=%r", url)
        return {"content": ""}
