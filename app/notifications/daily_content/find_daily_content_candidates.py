import uuid
from dataclasses import dataclass
from datetime import datetime

from app.notifications.notification_kinds import DAILY_CONTENT
from app.services.neon.db_conn import DBConn

# Early-morning "fresh topics are up" nudge, aimed at the commute window (users practice on the way to work, ~7:30-9am local), so it fires before they leave rather than after. A code constant (no per-user UI yet); the hourly scheduler can only target whole hours, so 7 over 8 to be ready before the early commute.
DAILY_CONTENT_HOUR_LOCAL = 7


@dataclass(frozen=True)
class DailyContentCandidate:
    user_id: uuid.UUID
    tokens: list[str]
    local_today: str  # 'YYYY-MM-DD', the per_kind_key (one nudge per local day)


async def find_daily_content_candidates(db: DBConn, now: datetime) -> list[DailyContentCandidate]:
    """Users whose local clock at `now` is the content-nudge hour, who want reminders, have a token, and haven't been nudged today.

    No "practiced today" filter: at 7am they almost never have, and a "new topics" nudge is fine even if they did. Whether there's fresh content to feature is decided in the sender (it fetches the headline once, content is global), so it isn't re-checked per user here."""
    rows = await db.fetch(
        """SELECT u.id AS user_id,
                  array_agg(DISTINCT d.apns_token) AS tokens,
                  to_char(($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date, 'YYYY-MM-DD') AS local_today
             FROM users u
             JOIN device_tokens d ON d.user_id = u.id
             LEFT JOIN notification_prefs p ON p.user_id = u.id
            WHERE u.deleted_at IS NULL
              AND COALESCE(p.reminders_enabled, TRUE)
              AND EXTRACT(HOUR FROM ($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))) = $2
              AND NOT EXISTS (
                    SELECT 1 FROM notification_log nl
                     WHERE nl.user_id = u.id AND nl.kind = $3
                       AND nl.per_kind_key = to_char(($1 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date, 'YYYY-MM-DD'))
            GROUP BY u.id, u.timezone""",
        now,
        DAILY_CONTENT_HOUR_LOCAL,
        DAILY_CONTENT,
    )
    return [
        DailyContentCandidate(
            user_id=row["user_id"],
            tokens=list(row["tokens"]),
            local_today=row["local_today"],
        )
        for row in rows
    ]
