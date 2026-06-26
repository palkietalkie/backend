import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.notifications.send_reminders import send_reminders
from app.notifications.send_streak_warning import send_streak_warning
from app.services.neon.get_neon_pool import get_neon_pool

logger = logging.getLogger(__name__)


async def run_reminder_scheduler() -> None:
    """Wake at the top of every hour and push reminders to users whose local clock just reached their reminder hour. Hourly granularity is enough, reminder_hour is a whole hour, and each user matches exactly one tick per local day (the dedup stamp guards against a restart re-running a tick)."""
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
            if daily or streak_warning:
                logger.info("reminders: pushed %d daily, %d streak-warning", daily, streak_warning)
        except Exception:
            logger.exception("reminder scheduler tick failed")
