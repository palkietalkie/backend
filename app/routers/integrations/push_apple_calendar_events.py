from datetime import UTC, datetime

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/integrations", tags=["integrations"])


class AppleCalendarEventIn(BaseModel):
    title: str
    start: datetime
    end: datetime | None = None
    location: str | None = None


@router.post("/apple-calendar/events", status_code=status.HTTP_204_NO_CONTENT)
async def push_apple_calendar_events(
    events: list[AppleCalendarEventIn],
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> None:
    # iOS pushes today's EventKit events here. We cache them implicitly via the Event analytics table so the conversation-start prompt can read them back. Full EventKit storage is TODO.
    now = datetime.now(UTC)
    for e in events:
        await db.execute(
            """INSERT INTO events (user_id, event_type, ts, props)
               VALUES ($1, $2, $3, $4)""",
            user["id"],
            "apple_calendar_event",
            now,
            {
                "title": e.title,
                "start": e.start.isoformat(),
                "end": e.end.isoformat() if e.end else None,
                "location": e.location,
            },
        )
