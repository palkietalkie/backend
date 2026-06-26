import uuid
from datetime import date, datetime

from app.notifications.build_reminder_push import build_reminder_alert
from app.notifications.choose_reminder import choose_reminder
from app.notifications.find_reminder_candidates import find_reminder_candidates
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn
from app.services.stats.compute_day_streak import compute_day_streak


async def send_reminders(db: DBConn, now: datetime) -> int:
    """One scheduler tick at `now`: push the right re-engagement reminder to each user whose local clock just hit their reminder hour, then stamp them so they aren't reminded again today. Returns how many users were pushed.

    The candidate query does the cheap filtering; the per-user decision (streak / comeback / practiced-today) happens here so a user who already practiced today gets nothing."""
    sent = 0
    for candidate in await find_reminder_candidates(db, now):
        practiced_today = candidate.last_practice_local_date == candidate.local_today
        days_since = (
            (candidate.local_today - candidate.last_practice_local_date).days
            if candidate.last_practice_local_date is not None
            else None
        )
        streak = await compute_day_streak(db, candidate.user_id)
        kind = choose_reminder(streak, days_since, practiced_today)
        if kind is None:
            continue
        alert = build_reminder_alert(kind, streak)
        for token in candidate.tokens:
            await send_push(token, alert)
        await _stamp_reminded(db, candidate.user_id, candidate.local_today)
        sent += 1
    return sent


async def _stamp_reminded(db: DBConn, user_id: uuid.UUID, local_today: date) -> None:
    # Upsert: the dedup stamp lives on the (possibly not-yet-existing) prefs row, so the hourly scheduler won't push this user again until their next local day.
    await db.execute(
        """INSERT INTO notification_prefs (user_id, last_reminded_on)
           VALUES ($1, $2)
           ON CONFLICT (user_id) DO UPDATE SET last_reminded_on = $2, updated_at = NOW()""",
        user_id,
        local_today,
    )
