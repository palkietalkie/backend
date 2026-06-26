import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.notifications.send_daily_content_nudge import send_daily_content_nudge
from app.notifications.send_reminders import send_reminders
from app.notifications.send_streak_warning import send_streak_warning
from app.notifications.send_weekly_recap import send_weekly_recap
from app.services.neon.get_neon_pool import get_neon_pool

logger = logging.getLogger(__name__)


async def run_reminder_scheduler() -> None:
    """Wake at the top of every hour and run each per-tick notification pass (daily reminder, streak warning, weekly recap, daily-content nudge). Every pass's candidate query matches users by their OWN local time, so hourly granularity is enough (the targets are whole hours), and the notification_log dedup guards against a restart re-running a tick."""
    while True:
        now = datetime.now(UTC)
        next_hour = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        await asyncio.sleep((next_hour - now).total_seconds())
        try:
            tick = datetime.now(UTC)
            pool = await get_neon_pool()
            async with pool.acquire() as conn:
                daily = await send_reminders(conn, tick)
                streak_warning = await send_streak_warning(conn, tick)
                weekly_recap = await send_weekly_recap(conn, tick)
                daily_content = await send_daily_content_nudge(conn, tick)
            if daily or streak_warning or weekly_recap or daily_content:
                logger.info(
                    "reminders: pushed %d daily, %d streak-warning, %d weekly-recap, %d daily-content",
                    daily,
                    streak_warning,
                    weekly_recap,
                    daily_content,
                )
        except Exception:
            logger.exception("reminder scheduler tick failed")
