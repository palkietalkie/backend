import uuid

from fastapi import APIRouter, Depends, Response, status

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])


@router.delete("/{persona_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_persona(
    persona_id: uuid.UUID,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> Response:
    async with db.transaction():
        deleted = await db.fetchval(
            """DELETE FROM persona_likes
               WHERE user_id = $1 AND persona_id = $2
               RETURNING id""",
            user["id"],
            persona_id,
        )
        if deleted is not None:
            db_persona = await fetch_persona_by_id(db, persona_id)
            if db_persona is not None:
                await db.execute(
                    """UPDATE personas
                       SET like_count = GREATEST(like_count - 1, 0), updated_at = NOW()
                       WHERE id = $1""",
                    persona_id,
                )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
