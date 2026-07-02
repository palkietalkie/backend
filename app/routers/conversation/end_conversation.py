import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.notifications.milestone.celebrate_streak_milestone import run_milestone_check
from app.routers.conversation.constants import INSERT_EVENT_SQL, SESSION_BY_USER_SQL
from app.routers.conversation.run_post_session_pipelines import run_post_session_pipelines
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.openai.compute_realtime_cost import compute_realtime_cost

router = APIRouter(prefix="/conversation", tags=["conversation"])


class EndRequest(BaseModel):
    # Summed OpenAI realtime usage for the whole session, reported by iOS from response.done events. Optional + defaulted so older clients that POST an empty body (and the PersonaPlex path, which has no such usage) still end cleanly, leaving the columns NULL rather than a wrong 0.
    input_tokens: int | None = None
    output_tokens: int | None = None


class EndResponse(BaseModel):
    session_id: uuid.UUID
    duration_seconds: int


@router.post("/{session_id}/end", response_model=EndResponse)
async def end_conversation(
    session_id: uuid.UUID,
    background: BackgroundTasks,
    body: EndRequest = EndRequest(),
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

    # Derive $ cost from the reported tokens x the session model's audio rate. None (stored NULL) for PersonaPlex or a session that reported no usage, never a misleading 0.
    cost = compute_realtime_cost(session_row["model"], body.input_tokens, body.output_tokens)
    input_cost, output_cost = cost if cost is not None else (None, None)

    async with db.transaction():
        await db.execute(
            """UPDATE conversation_sessions
               SET ended_at = $2, duration_seconds = $3,
                   input_tokens = $4, output_tokens = $5,
                   input_cost_usd = $6, output_cost_usd = $7
               WHERE id = $1""",
            session_id,
            now,
            duration,
            body.input_tokens,
            body.output_tokens,
            input_cost,
            output_cost,
        )
        await db.execute(
            INSERT_EVENT_SQL,
            user["id"],
            "conversation_end",
            now,
            {"session_id": str(session_id), "duration_seconds": duration},
        )

    background.add_task(run_post_session_pipelines, session_id, user["id"])
    # This session may have just extended the streak onto a milestone (7/30/...); celebrate it off the request path.
    background.add_task(run_milestone_check, user["id"])
    return EndResponse(session_id=session_id, duration_seconds=duration)
