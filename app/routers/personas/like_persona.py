import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.auth.resolve_current_user import resolve_current_user
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.get_db import get_db
from app.services.neon.rows import PersonaRow, UserRow

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("/{persona_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_persona(
    persona_id: uuid.UUID,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> Response:
    is_preset = find_preset_by_id(persona_id) is not None
    db_persona: PersonaRow | None = None
    if not is_preset:
        db_persona = await fetch_persona_by_id(db, persona_id)
        if db_persona is None or (
            not db_persona["is_public"] and db_persona["user_id"] != user["id"]
        ):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="persona not found")

    async with db.transaction():
        inserted = await db.fetchval(
            """INSERT INTO persona_likes (id, user_id, persona_id)
               VALUES ($1, $2, $3)
               ON CONFLICT ON CONSTRAINT uq_like_user_persona DO NOTHING
               RETURNING id""",
            uuid.uuid4(),
            user["id"],
            persona_id,
        )
        # ON CONFLICT DO NOTHING + RETURNING id: when a row was inserted we get the new id, otherwise NULL. Only bump the like_count on a fresh insert.
        if inserted is not None and db_persona is not None:
            await db.execute(
                """UPDATE personas
                   SET like_count = like_count + 1, updated_at = NOW()
                   WHERE id = $1""",
                persona_id,
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
