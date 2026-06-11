from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/stats", tags=["stats"])


class MistakeOut(BaseModel):
    original: str
    corrected: str
    category: str
    count: int
    last_seen_at: datetime


@router.get("/mistakes", response_model=list[MistakeOut])
async def list_mistakes(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[MistakeOut]:
    rows = await db.fetch(
        """SELECT id, user_id, original, corrected, category, count, last_seen_at
           FROM mistakes
           WHERE user_id = $1
           ORDER BY count DESC, last_seen_at DESC
           LIMIT $2 OFFSET $3""",
        user["id"],
        limit,
        offset,
    )
    return [
        MistakeOut(
            original=row["original"],
            corrected=row["corrected"],
            category=row["category"],
            count=row["count"],
            last_seen_at=row["last_seen_at"],
        )
        for row in rows
    ]
