from datetime import datetime

from app.notifications.build_weekly_recap_alert import build_weekly_recap_alert
from app.notifications.find_weekly_recap_candidates import find_weekly_recap_candidates
from app.notifications.notification_kinds import WEEKLY_RECAP
from app.notifications.record_notification import record_notification
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn
from app.services.stats.compute_day_streak import compute_day_streak


async def send_weekly_recap(db: DBConn, now: datetime) -> int:
    """Weekly-recap pass for one scheduler tick at `now`: push "you practiced N times this week, M min, S-day streak" to each user who reached their Sunday recap hour, then stamp them. Returns how many were pushed.

    Only users who practiced at least once in the last 7 local days get a recap, a zero-session recap would demotivate (lapsed users get the comeback nudge instead). Minutes is floored to >= 1 so a real sub-minute session never reads as '0 min' (duration_seconds is null for abnormally-ended sessions, hence the COALESCE)."""
    sent = 0
    for candidate in await find_weekly_recap_candidates(db, now):
        stats = await db.fetchrow(
            """SELECT count(*) AS sessions,
                      COALESCE(sum(s.duration_seconds), 0) AS seconds
                 FROM conversation_sessions s
                 JOIN users u ON u.id = s.user_id
                WHERE s.user_id = $1
                  AND (s.started_at AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date
                      > ($2 AT TIME ZONE COALESCE(u.timezone, 'UTC'))::date - 7""",
            candidate.user_id,
            now,
        )
        sessions = stats["sessions"] if stats else 0
        if not sessions:
            continue  # nothing to celebrate; the comeback nudge covers inactive users
        minutes = max(1, round((stats["seconds"] if stats else 0) / 60))
        streak = await compute_day_streak(db, candidate.user_id)
        alert = build_weekly_recap_alert(sessions, minutes, streak)
        for token in candidate.tokens:
            await send_push(token, alert)
        await record_notification(db, candidate.user_id, WEEKLY_RECAP, candidate.iso_week)
        sent += 1
    return sent
