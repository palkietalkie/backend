"""GET /recall/facts — Neo4j KG lookup, called when the realtime model invokes the recall_facts tool mid-conversation.

The endpoint exists because the KG lives server-side (Neo4j creds + driver are backend-only) and iOS — which receives the model's tool call over its direct iOS↔OpenAI WebSocket — has no other way to reach it. This is the authenticated boundary: Clerk JWT → resolve_current_user scopes the query to that user, then delegates to the service. Thin on purpose (logic lives in search_entities). Best-effort: a dead dependency returns empty, never an error, so a tool call can't stall the live conversation.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.auth.resolve_current_user import resolve_current_user
from app.services.neo4j.search_entities import search_entities
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/recall", tags=["recall"])
logger = logging.getLogger(__name__)


@router.get("/facts")
async def recall_facts(
    q: str = Query(..., min_length=1, max_length=200),
    user: UserRow = Depends(resolve_current_user),
) -> dict[str, Any]:
    try:
        return {"entities": await search_entities(user["id"], q)}
    except Exception:
        logger.exception("recall_facts failed for q=%r", q)
        return {"entities": []}
