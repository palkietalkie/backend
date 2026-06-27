from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/notification-prefs", tags=["notification-prefs"])

# Defaults a user with no notification_prefs row reads as. They mirror the COALESCE fallbacks the scheduler's candidate queries use, so GET (before any PUT) reports exactly what the scheduler would act on.
DEFAULT_REMINDERS_ENABLED = True
DEFAULT_REMINDER_HOUR_LOCAL = 19


class NotificationPrefsOut(BaseModel):
    reminders_enabled: bool
    reminder_hour_local: int


@router.get("", response_model=NotificationPrefsOut)
async def fetch_notification_prefs(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> NotificationPrefsOut:
    row = await db.fetchrow(
        "SELECT reminders_enabled, reminder_hour_local FROM notification_prefs WHERE user_id = $1",
        user["id"],
    )
    if row is None:
        return NotificationPrefsOut(
            reminders_enabled=DEFAULT_REMINDERS_ENABLED,
            reminder_hour_local=DEFAULT_REMINDER_HOUR_LOCAL,
        )
    return NotificationPrefsOut(
        reminders_enabled=row["reminders_enabled"],
        reminder_hour_local=row["reminder_hour_local"],
    )
