from datetime import datetime

from app.notifications.daily_content.build_daily_content_alert import build_daily_content_alert
from app.notifications.daily_content.find_daily_content_candidates import (
    find_daily_content_candidates,
)
from app.notifications.notification_kinds import DAILY_CONTENT
from app.notifications.record_notification import record_notification
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn


async def send_daily_content_nudge(db: DBConn, now: datetime) -> int:
    """Daily-content pass for one scheduler tick at `now`: push "Did you catch this? <headline>" to each user who reached their morning content hour, then stamp them. Returns how many were pushed.

    The headline is fetched ONCE (content is global, refreshed daily by UTC day), so all candidates share it and we make one content query per tick, not per user. No fresh headline → no content to feature → send nothing."""
    headline = await db.fetchval(
        """SELECT dc.items->0->>'title'
             FROM daily_content dc
            WHERE dc.day >= ($1 AT TIME ZONE 'UTC')::date - 1
              AND dc.items <> '[]'::jsonb
              AND dc.topic <> 'quizzes'
            ORDER BY dc.day DESC, dc.topic
            LIMIT 1""",
        now,
    )
    if not headline:
        return 0
    alert = build_daily_content_alert(headline)
    sent = 0
    for candidate in await find_daily_content_candidates(db, now):
        for token in candidate.tokens:
            await send_push(token, alert)
        await record_notification(db, candidate.user_id, DAILY_CONTENT, candidate.local_today)
        sent += 1
    return sent
