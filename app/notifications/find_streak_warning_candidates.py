import uuid
from dataclasses import dataclass
from datetime import date, datetime

from app.notifications.notification_kinds import STREAK_WARNING
from app.services.neon.db_conn import DBConn

# Late-evening "last chance before midnight breaks the streak". A code constant (no per-user UI yet), distinct from the daily reminder hour so a streak-holder can get both nudges on the same day.
STREAK_WARNING_HOUR_LOCAL = 21


@dataclass(frozen=True)
class StreakWarningCandidate:
    user_id: uuid.UUID
    tokens: list[str]
    local_today: date
    last_practice_local_date: date | None


async def find_streak_warning_candidates(db: DBConn, now: datetime) -> list[StreakWarningCandidate]:
    """Users whose local clock at `now` is the streak-warning hour, who want reminders, have a token, and haven't had an streak-warning push yet today (its own dedup, separate from the daily reminder's).

    Whether they have a LIVE streak and actually skipped today is decided per-candidate in the job (streak is derived via compute_day_streak, not in SQL). Mirrors find_reminder_candidates with the streak-warning hour; its own-day dedup is a NOT EXISTS against notification_log under the streak_warning kind, separate from the daily reminder's, so a streak-holder can get both nudges on the same day."""
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
              AND EXTRACT(HOUR FROM ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))) = $2
              AND NOT EXISTS (
                    SELECT 1 FROM notification_log nl
                     WHERE nl.user_id = u.id AND nl.kind = $3
                       AND nl.per_kind_key = ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date::text)
            GROUP BY u.id, u.timezone""",
        now,
        STREAK_WARNING_HOUR_LOCAL,
        STREAK_WARNING,
    )
    return [
        StreakWarningCandidate(
            user_id=row["user_id"],
            tokens=list(row["tokens"]),
            local_today=row["local_today"],
            last_practice_local_date=row["last_practice"],
        )
        for row in rows
    ]
