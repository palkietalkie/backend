import uuid

from app.notifications.milestone.build_milestone_alert import build_milestone_alert
from app.notifications.milestone.is_streak_milestone import is_streak_milestone
from app.notifications.notification_kinds import MILESTONE
from app.notifications.record_notification import record_notification
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_pool import get_neon_pool
from app.services.stats.compute_day_streak import compute_day_streak


async def celebrate_streak_milestone(db: DBConn, user_id: uuid.UUID) -> bool:
    """Push a celebration IF the just-ended session pushed the user's streak onto a milestone not yet celebrated. Returns whether a push fired.

    Idempotent: the streak number is the per_kind_key, so a second session the same day (streak unchanged) finds the milestone already logged and won't re-fire. Honors the reminders toggle (a user who silenced notifications shouldn't get these either)."""
    streak = await compute_day_streak(db, user_id)
    if not is_streak_milestone(streak):
        return False
    prefs = await db.fetchrow(
        "SELECT reminders_enabled FROM notification_prefs WHERE user_id = $1",
        user_id,
    )
    if prefs is not None and not prefs["reminders_enabled"]:
        return False
    per_kind_key = str(streak)
    already = await db.fetchval(
        "SELECT 1 FROM notification_log WHERE user_id = $1 AND kind = $2 AND per_kind_key = $3",
        user_id,
        MILESTONE,
        per_kind_key,
    )
    if already is not None:
        return False

    tokens = await db.fetch("SELECT apns_token FROM device_tokens WHERE user_id = $1", user_id)
    alert = build_milestone_alert(streak)
    for row in tokens:
        await send_push(row["apns_token"], alert)
    await record_notification(db, user_id, MILESTONE, per_kind_key)
    return True


async def run_milestone_check(user_id: uuid.UUID) -> None:
    """Session-end background entrypoint: acquires its own connection (the request's is gone by the time background tasks run) and celebrates a new milestone if there is one."""
    pool = await get_neon_pool()
    async with pool.acquire() as conn:
        await celebrate_streak_milestone(conn, user_id)
