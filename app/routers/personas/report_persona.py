import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.personas.presets.find_preset_by_id import find_preset_by_id
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])

# Distinct reporters that hide a community persona from EVERYONE (see list_personas). A single report already hides the persona for that reporter alone; this is the higher bar for a global takedown, set high enough that a small ring of bad actors can't bury someone else's persona.
REPORT_HIDE_THRESHOLD = 10


class ReportPersonaIn(BaseModel):
    reason: str | None = None


@router.post("/{persona_id}/report", status_code=status.HTTP_204_NO_CONTENT)
async def report_persona(
    persona_id: uuid.UUID,
    body: ReportPersonaIn | None = None,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> Response:
    if find_preset_by_id(persona_id) is not None:
        # Presets are first-party content, not user-generated — nothing to moderate.
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="presets can't be reported"
        )
    persona = await fetch_persona_by_id(db, persona_id)
    if persona is None or not persona["is_public"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="persona not found")
    if persona["user_id"] == user["id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="can't report your own persona"
        )
    # Idempotent: a user reporting the same persona twice is a no-op (one row per user via the unique constraint).
    await db.execute(
        """INSERT INTO persona_reports (id, user_id, persona_id, reason)
           VALUES ($1, $2, $3, $4)
           ON CONFLICT ON CONSTRAINT uq_report_user_persona DO NOTHING""",
        uuid.uuid4(),
        user["id"],
        persona_id,
        body.reason if body else None,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
