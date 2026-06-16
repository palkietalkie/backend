import asyncio

from app.daily_content.fetch_article_details import fetch_article_details
from app.daily_content.models import TalkItem


async def enrich_news_details(items: list[TalkItem], *, max_chars: int = 4000) -> list[TalkItem]:
    """Fetch every news item's full article body concurrently so the model gets real depth, not just NewsAPI's one-line description.

    Runs at daily-content generation time (the cron), so the per-article fetch latency is off the user's conversation path.
    """
    return list(await asyncio.gather(*(fetch_article_details(item, max_chars) for item in items)))
