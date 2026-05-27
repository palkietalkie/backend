"""Knowledge graph viewer (read-only).

User cannot edit. KG is populated by the post-session `kg_extraction` pipeline.
"""

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neo4j.fetch_kg import fetch_kg as fetch_kg_from_neo4j
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/kg", tags=["kg"])


class KGResponse(BaseModel):
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


@router.get("", response_model=KGResponse)
async def fetch_kg(user: UserRow = Depends(resolve_current_user)) -> KGResponse:
    data = await fetch_kg_from_neo4j(user["id"])
    return KGResponse(nodes=data["nodes"], edges=data["edges"])
