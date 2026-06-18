import asyncio
import logging
from datetime import UTC, datetime

from app.daily_content.dedup_news_across_categories import dedup_news_across_categories
from app.daily_content.enrich_news_details import enrich_news_details
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
    # Pull each article's full body now, off the user's path, so the conversation prompt carries real depth rather than NewsAPI's one-line blurb.
    politics, business, sports = await asyncio.gather(
        enrich_news_details(politics),
        enrich_news_details(business),
        enrich_news_details(sports),
    )
    politics, business, sports = dedup_news_across_categories([politics, business, sports])
    seed_titles = [item.title for item in (politics + business + sports)[:5]]
    # Quizzes depend on an external LLM (Gemma); a transient failure there must NOT lose the day's news, so degrade to no quizzes instead of aborting the whole refresh.
    try:
        quizzes = await generate_quizzes(seed_titles)
    except Exception:  # noqa: BLE001 — any quiz-generation failure should still let news persist
        logger.exception("quiz generation failed; saving news without quizzes")
        quizzes = []

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
