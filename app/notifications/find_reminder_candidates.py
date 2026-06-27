import uuid
from dataclasses import dataclass
from datetime import date, datetime

from app.notifications.notification_kinds import DAILY_REMINDER
from app.services.neon.db_conn import DBConn


@dataclass(frozen=True)
class ReminderCandidate:
    user_id: uuid.UUID
    tokens: list[str]
    local_today: date
    last_practice_local_date: date | None


async def find_reminder_candidates(db: DBConn, now: datetime) -> list[ReminderCandidate]:
    """Users whose local clock at `now` is at their reminder hour, who want reminders, have a device token, and haven't been reminded yet today.

    `now` is passed in (not SQL `now()`) so the scheduler controls the tick time and tests are deterministic. This only narrows the set cheaply; the actual send decision (streak / practiced-today / comeback) is per-candidate in the job. Timezone, enable flag, and reminder hour all fall back to defaults so a user with no notification_prefs row is still considered. "Not reminded today" is a NOT EXISTS against notification_log (per_kind_key = the user's local date)."""
    rows = await db.fetch(
        """SELECT u.id AS user_id,
                  array_agg(DISTINCT d.apns_token) AS tokens,
                  ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date AS local_today,
                  (SELECT max((s.started_at AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date)
                     FROM conversation_sessions s
                    WHERE s.user_id = u.id) AS last_practice
             FROM users u
             JOIN device_tokens d ON d.user_id = u.id
             LEFT JOIN notification_prefs p ON p.user_id = u.id
            WHERE u.deleted_at IS NULL
              AND COALESCE(p.reminders_enabled, TRUE)
              AND EXTRACT(HOUR FROM ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC')))
                  = COALESCE(p.reminder_hour_local, 19)
              AND NOT EXISTS (
                    SELECT 1 FROM notification_log nl
                     WHERE nl.user_id = u.id AND nl.kind = $2
                       AND nl.per_kind_key = ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date::text)
            GROUP BY u.id, u.timezone""",
        now,
        DAILY_REMINDER,
    )
    return [
        ReminderCandidate(
            user_id=row["user_id"],
            tokens=list(row["tokens"]),
            local_today=row["local_today"],
            last_practice_local_date=row["last_practice"],
        )
        for row in rows
    ]
