import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.routers.conversation.constants import INSERT_EVENT_SQL, SESSION_BY_USER_SQL
from app.routers.conversation.run_post_session_pipelines import run_post_session_pipelines
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/conversation", tags=["conversation"])


class EndResponse(BaseModel):
    session_id: uuid.UUID
    duration_seconds: int


@router.post("/{session_id}/end", response_model=EndResponse)
async def end_conversation(
    session_id: uuid.UUID,
    background: BackgroundTasks,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> EndResponse:
    session_row = await db.fetchrow(SESSION_BY_USER_SQL, session_id, user["id"])
    if session_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="session not found")

    now = datetime.now(UTC)
    started = session_row["started_at"]
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    duration = max(int((now - started).total_seconds()), 0)

    async with db.transaction():
        await db.execute(
            """UPDATE conversation_sessions
               SET ended_at = $2, duration_seconds = $3
               WHERE id = $1""",
            session_id,
            now,
            duration,
        )
        await db.execute(
            INSERT_EVENT_SQL,
            user["id"],
            "conversation_end",
            now,
            {"session_id": str(session_id), "duration_seconds": duration},
        )

    background.add_task(run_post_session_pipelines, session_id, user["id"])
    return EndResponse(session_id=session_id, duration_seconds=duration)
