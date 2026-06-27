from datetime import datetime

from app.notifications.build_streak_warning_alert import build_streak_warning_alert
from app.notifications.find_streak_warning_candidates import find_streak_warning_candidates
from app.notifications.notification_kinds import STREAK_WARNING
from app.notifications.record_notification import record_notification
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn
from app.services.stats.compute_day_streak import compute_day_streak


async def send_streak_warning(db: DBConn, now: datetime) -> int:
    """Streak-warning pass for one scheduler tick at `now`: push "your N-day streak ends tonight" to streak-holders who reached the streak-warning hour without practicing today, then stamp them. Returns how many were pushed.

    Fires only for a LIVE streak the user hasn't already extended today, a 0 streak has no streak to lose, and someone who practiced today is safe."""
    sent = 0
    for candidate in await find_streak_warning_candidates(db, now):
        if candidate.last_practice_local_date == candidate.local_today:
            continue  # already practiced today; streak is safe
        streak = await compute_day_streak(db, candidate.user_id)
        if streak <= 0:
            continue  # no live streak to lose
        alert = build_streak_warning_alert(streak)
        for token in candidate.tokens:
            await send_push(token, alert)
        await record_notification(
            db, candidate.user_id, STREAK_WARNING, candidate.local_today.isoformat()
        )
        sent += 1
    return sent
