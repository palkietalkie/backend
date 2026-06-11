import asyncio
import logging
from datetime import UTC, datetime, time, timedelta

from app.pipelines.daily_content.constants import TOPICS
from app.pipelines.daily_content.refresh_daily_content import refresh_daily_content
from app.services.daily_content.load_today_topics import load_today_topics
from app.services.neon.get_neon_pool import get_neon_pool

logger = logging.getLogger(__name__)

# 06:00 UTC = ~11pm Pacific the previous day = ~3pm Tokyo. Content is ready before morning use in both regions. Anchor in UTC so DST changes don't drift the schedule.
REFRESH_HOUR_UTC = 6


async def run_daily_content_scheduler() -> None:
    try:
        pool = await get_neon_pool()
        async with pool.acquire() as conn:
            existing = await load_today_topics(conn)
        missing = [t for t in TOPICS if not existing.get(t)]
        if missing:
            logger.info("daily_content missing topics %s on startup; refreshing now", missing)
            await refresh_daily_content()
    except Exception:
        logger.exception("daily_content startup catch-up failed")

    while True:
        now = datetime.now(UTC)
        target = datetime.combine(now.date(), time(REFRESH_HOUR_UTC, 0), tzinfo=UTC)
        if target <= now:
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        logger.info(
            "daily_content next refresh at %s (in %.0fs)", target.isoformat(), sleep_seconds
        )
        await asyncio.sleep(sleep_seconds)
        try:
            await refresh_daily_content()
        except Exception:
            logger.exception("daily_content scheduled refresh failed")
