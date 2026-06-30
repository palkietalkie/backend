"""DELETE /kg/{entity_id} — soft-delete a wrong knowledge-graph entity the user swiped away on the KG screen."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.resolve_current_user import resolve_current_user
from app.services.neo4j.remove_kg_entity import remove_kg_entity as remove_kg_entity_from_neo4j
from app.services.neon.rows import UserRow

_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kg", tags=["kg"])


@router.delete("/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_kg_entity(entity_id: str, user: UserRow = Depends(resolve_current_user)) -> None:
    # Surface a failure (vs swallowing) so iOS can revert its optimistic removal and the user can retry, rather than the entity silently reappearing on the next load.
    try:
        await remove_kg_entity_from_neo4j(user["id"], entity_id)
    except Exception as exc:
        _logger.exception("knowledge-graph entity removal failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Couldn't remove that entity right now. Try again.",
        ) from exc
