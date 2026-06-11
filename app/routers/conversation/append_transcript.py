import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.routers.conversation.constants import SESSION_BY_USER_SQL
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/conversation", tags=["conversation"])


class TranscriptAppend(BaseModel):
    speaker: str = Field(pattern="^(user|persona)$")
    text: str
    started_at: datetime
    ended_at: datetime


@router.post("/{session_id}/transcript", status_code=status.HTTP_204_NO_CONTENT)
async def append_transcript(
    session_id: uuid.UUID,
    body: TranscriptAppend,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> None:
    session_row = await db.fetchrow(SESSION_BY_USER_SQL, session_id, user["id"])
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, $2, $3, $4, $5)""",
        session_id,
        body.speaker,
        body.text,
        body.started_at,
        body.ended_at,
    )
