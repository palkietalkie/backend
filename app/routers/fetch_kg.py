"""Knowledge graph viewer (read-only).

User cannot edit. KG is populated by the post-session `kg_extraction` pipeline.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neo4j.fetch_kg import fetch_kg as fetch_kg_from_neo4j
from app.services.neon.rows import UserRow

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg", tags=["kg"])


class KGResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@router.get("", response_model=KGResponse)
async def fetch_kg(user: UserRow = Depends(resolve_current_user)) -> KGResponse:
    # AuraDB (free tier) pauses when idle and can time out. A read-only viewer must never 500 the client over it — degrade to an empty graph so the rest of the screen still works.
    try:
        data = await fetch_kg_from_neo4j(user["id"])
    except Exception:
        _logger.exception("knowledge-graph fetch failed; returning an empty graph")
        return KGResponse(nodes=[], edges=[])
    return KGResponse(nodes=data["nodes"], edges=data["edges"])
