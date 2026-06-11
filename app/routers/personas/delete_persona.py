import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.resolve_current_user import resolve_current_user
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: uuid.UUID,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> Response:
    if find_preset_by_id(persona_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="presets are read-only",
        )
    persona = await fetch_persona_by_id(db, persona_id)
    if persona is None or persona["user_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="persona not found")
    await db.execute(
        "DELETE FROM personas WHERE id = $1 AND user_id = $2",
        persona_id,
        user["id"],
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
