import uuid
from dataclasses import dataclass
from datetime import datetime

from app.notifications.notification_kinds import WEEKLY_RECAP
from app.services.neon.db_conn import DBConn

# Sunday-evening recap of the week just finished. Code constants (no per-user UI yet). EXTRACT(DOW) returns 0 for Sunday.
WEEKLY_RECAP_HOUR_LOCAL = 18
WEEKLY_RECAP_DOW = 0


@dataclass(frozen=True)
class WeeklyRecapCandidate:
    user_id: uuid.UUID
    tokens: list[str]
    iso_week: str


async def find_weekly_recap_candidates(db: DBConn, now: datetime) -> list[WeeklyRecapCandidate]:
    """Users whose local clock at `now` is the weekly-recap moment (Sunday, recap hour), who want reminders, have a token, and haven't had this week's recap yet.

    Whether they actually practiced this week (and the stat values) is decided per-candidate in the job. Dedup is per ISO week via notification_log (kind=weekly_recap, per_kind_key=the local ISO week)."""
    rows = await db.fetch(
        # The 'IYYY"-W"IW' mask renders the local ISO week, e.g. '2026-W26'. It is computed SQL-side in BOTH the returned key and the dedup check so they always match (the per_kind_key the sender stamps is this same value).
        """SELECT u.id AS user_id,
                  array_agg(DISTINCT d.apns_token) AS tokens,
                  to_char(($1 AT TIME ZONE COALESCE(u.timezone, 'UTC')), 'IYYY"-W"IW') AS iso_week
             FROM users u
             JOIN device_tokens d ON d.user_id = u.id
             LEFT JOIN notification_prefs p ON p.user_id = u.id
            WHERE u.deleted_at IS NULL
              AND COALESCE(p.reminders_enabled, TRUE)
              AND EXTRACT(DOW FROM ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))) = $2
              AND EXTRACT(HOUR FROM ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))) = $3
              AND NOT EXISTS (
                    SELECT 1 FROM notification_log nl
                     WHERE nl.user_id = u.id AND nl.kind = $4
                       AND nl.per_kind_key = to_char(($1 AT TIME ZONE COALESCE(u.timezone, 'UTC')), 'IYYY"-W"IW'))
            GROUP BY u.id, u.timezone""",
        now,
        WEEKLY_RECAP_DOW,
        WEEKLY_RECAP_HOUR_LOCAL,
        WEEKLY_RECAP,
    )
    return [
        WeeklyRecapCandidate(
            user_id=row["user_id"],
            tokens=list(row["tokens"]),
            iso_week=row["iso_week"],
        )
        for row in rows
    ]
