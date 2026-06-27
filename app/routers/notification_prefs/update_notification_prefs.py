from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.routers.notification_prefs.fetch_notification_prefs import (
    DEFAULT_REMINDERS_ENABLED,
    NotificationPrefsOut,
)
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.slack.format_user_label import format_user_label
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/notification-prefs", tags=["notification-prefs"])


class NotificationPrefsUpdate(BaseModel):
    reminders_enabled: bool
    reminder_hour_local: int = Field(ge=0, le=23)


@router.put("", response_model=NotificationPrefsOut)
async def update_notification_prefs(
    body: NotificationPrefsUpdate,
    background_tasks: BackgroundTasks,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> NotificationPrefsOut:
    # Prior enabled state, to detect the OFF transition. A user with no row defaults to enabled (matches the scheduler).
    prior = await db.fetchval(
        "SELECT reminders_enabled FROM notification_prefs WHERE user_id = $1", user["id"]
    )
    was_enabled = prior if prior is not None else DEFAULT_REMINDERS_ENABLED

    await db.execute(
        """INSERT INTO notification_prefs (user_id, reminders_enabled, reminder_hour_local, updated_at)
           VALUES ($1, $2, $3, NOW())
           ON CONFLICT (user_id) DO UPDATE
             SET reminders_enabled = $2, reminder_hour_local = $3, updated_at = NOW()""",
        user["id"],
        body.reminders_enabled,
        body.reminder_hour_local,
    )

    # Turning reminders OFF is the churn signal we want in real time. Fire-and-forget AFTER the response so the Slack POST never slows the settings save; post_message no-ops outside production.
    if was_enabled and not body.reminders_enabled:
        background_tasks.add_task(
            post_message,
            get_settings().slack_channel_gtm,
            f":no_bell: *notifications_off* — {format_user_label(user)} turned reminders off",
        )

    return NotificationPrefsOut(
        reminders_enabled=body.reminders_enabled,
        reminder_hour_local=body.reminder_hour_local,
    )
