import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.resolve_current_user import resolve_current_user
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.routers.personas.build_patch_sql import PersonaUpdate, build_patch_sql
from app.routers.personas.build_persona_out_from_preset import PersonaOut
from app.routers.personas.build_persona_out_from_row import build_persona_out_from_row
from app.routers.personas.list_personas import LIKED_BY_USER_SQL
from app.routers.personas.validate_voice import validate_voice
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])


@router.patch("/{persona_id}", response_model=PersonaOut)
async def update_persona(
    persona_id: uuid.UUID,
    body: PersonaUpdate,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> PersonaOut:
    if find_preset_by_id(persona_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="presets are read-only; create a custom persona instead",
        )
    persona = await fetch_persona_by_id(db, persona_id)
    if persona is None or persona["user_id"] != user["id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="persona not found")
    if body.voice_id is not None:
        validate_voice(body.voice_id)

    sql, values = build_patch_sql(persona, body)
    if sql:
        row = await db.fetchrow(sql, *values)
        assert row is not None
        persona = dict(row)  # type: ignore[assignment]

    liked_rows = await db.fetch(LIKED_BY_USER_SQL, user["id"])
    liked_ids: set[uuid.UUID] = {row["persona_id"] for row in liked_rows}
    assert persona is not None
    return build_persona_out_from_row(persona, user_id=user["id"], liked_ids=liked_ids)  # type: ignore[arg-type]
