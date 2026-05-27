"""Client-side telemetry endpoint.

iOS posts events here so we can compute aggregate stats (e.g., cold-start
percentiles) without paying for an external analytics vendor. Events land in
the same `events` table backend pipelines write to, so dashboards can mix
client and server signals.
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/events", tags=["events"])


class EventIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    # Free-form structured payload. For cold-start: {"duration_ms": 5234, "phase_timings": {...}}.
    props: dict[str, Any] = Field(default_factory=lambda: {})
    # Optional client-side timestamp. Server stamps `ts` either way; this lets the client report when the event actually happened (handles offline replay).  # noqa: E501
    client_ts: datetime | None = None


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def record_event(
    body: EventIn,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> None:
    await db.execute(
        """INSERT INTO events (user_id, event_type, ts, props)
           VALUES ($1, $2, $3, $4)""",
        user["id"],
        body.event_type,
        body.client_ts or datetime.now(UTC),
        body.props,
    )
