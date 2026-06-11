from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/stats", tags=["stats"])


class PhraseOut(BaseModel):
    phrase: str
    count: int
    last_used_at: datetime


@router.get("/phrases", response_model=list[PhraseOut])
async def list_phrases(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[PhraseOut]:
    rows = await db.fetch(
        """SELECT user_id, phrase, count, last_used_at
           FROM phrase_freq
           WHERE user_id = $1
           ORDER BY count DESC, last_used_at DESC
           LIMIT $2 OFFSET $3""",
        user["id"],
        limit,
        offset,
    )
    return [
        PhraseOut(phrase=row["phrase"], count=row["count"], last_used_at=row["last_used_at"])
        for row in rows
    ]
