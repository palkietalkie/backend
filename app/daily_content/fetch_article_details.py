from dataclasses import replace

from app.daily_content.models import TalkItem
from app.services.http.fetch_url_text import fetch_url_text


async def fetch_article_details(item: TalkItem, max_chars: int) -> TalkItem:
    """Return the item with its full article body fetched into `details`.

    An item with no URL, or whose fetch returns nothing, keeps details="" so the prompt falls back to its summary.
    """
    if not item.url:
        return item
    body = await fetch_url_text(item.url, max_chars=max_chars)
    return replace(item, details=body) if body else item
