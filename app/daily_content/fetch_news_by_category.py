import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.daily_content.models import TalkItem


class _Source(BaseModel):
    name: str = ""


class _Article(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    urlToImage: str | None = None  # noqa: N815 — matches NewsAPI's camelCase field name verbatim
    source: _Source | None = None


class _NewsResponse(BaseModel):
    articles: list[_Article] = []


async def fetch_news_by_category(category: str) -> list[TalkItem]:
    """Pull the top 10 NewsAPI headlines for a category (politics / business / sports / …) and map them to TalkItems.

    Single source for what used to be three near-identical files (fetch_politics, fetch_business, fetch_sports).
    """
    settings = get_settings()
    if not settings.news_api_key:
        return []
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "language": "en", "category": category, "pageSize": 10},
            headers={"X-Api-Key": settings.news_api_key},
        )
        resp.raise_for_status()
        data = resp.json()
    try:
        parsed = _NewsResponse.model_validate(data)
    except ValidationError:
        return []
    out: list[TalkItem] = []
    for art in parsed.articles[:10]:
        if not art.title:
            continue
        out.append(
            TalkItem(
                title=art.title,
                summary=art.description or "",
                source=art.source.name if art.source else "",
                image_url=art.urlToImage or "",
                url=art.url or "",
            )
        )
    return out
