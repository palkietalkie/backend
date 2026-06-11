import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/conversation", tags=["conversation"])


class SessionSummary(BaseModel):
    session_id: uuid.UUID
    persona_id: uuid.UUID | None
    started_at: datetime
    ended_at: datetime | None
    duration_seconds: int | None


@router.get("/sessions", response_model=list[SessionSummary])
async def list_sessions(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
    limit: int = 100,
) -> list[SessionSummary]:
    rows = await db.fetch(
        """SELECT id, persona_id, started_at, ended_at, duration_seconds
           FROM conversation_sessions
           WHERE user_id = $1
           ORDER BY started_at DESC
           LIMIT $2""",
        user["id"],
        limit,
    )
    return [
        SessionSummary(
            session_id=row["id"],
            persona_id=row["persona_id"],
            started_at=row["started_at"],
            ended_at=row["ended_at"],
            duration_seconds=row["duration_seconds"],
        )
        for row in rows
    ]
