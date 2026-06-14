import asyncio
import logging
from datetime import UTC, datetime

from app.daily_content.fetch_news_by_category import fetch_news_by_category
from app.daily_content.generate_quizzes import generate_quizzes
from app.services.daily_content.save_topic_items import save_topic_items
from app.services.neon.get_neon_pool import get_neon_pool

logger = logging.getLogger(__name__)


async def refresh_daily_content() -> None:
    # UTC, NOT local. Fly runs UTC; a local dev run would otherwise write a different date row from what the API serves.
    today = datetime.now(UTC).date()
    politics, business, sports = await asyncio.gather(
        fetch_news_by_category("politics"),
        fetch_news_by_category("business"),
        fetch_news_by_category("sports"),
    )
    seed_titles = [item.title for item in (politics + business + sports)[:5]]
    quizzes = await generate_quizzes(seed_titles)

    pool = await get_neon_pool()
    async with pool.acquire() as conn:
        await save_topic_items(today, "politics", politics, conn)
        await save_topic_items(today, "business", business, conn)
        await save_topic_items(today, "sports", sports, conn)
        await save_topic_items(today, "quizzes", quizzes, conn)
    logger.info(
        "daily_content refreshed day=%s politics=%d business=%d sports=%d quizzes=%d",
        today,
        len(politics),
        len(business),
        len(sports),
        len(quizzes),
    )
