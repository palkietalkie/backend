import httpx
from pydantic import BaseModel, ValidationError

from app.config import get_settings
from app.pipelines.daily_content.models import NewsStory


class _Source(BaseModel):
    name: str = ""


class _Article(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    source: _Source | None = None


class _NewsResponse(BaseModel):
    articles: list[_Article] = []


async def fetch_news() -> list[NewsStory]:
    settings = get_settings()
    if not settings.news_api_key:
        return []
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "language": "en", "pageSize": 10},
            headers={"X-Api-Key": settings.news_api_key},
        )
        resp.raise_for_status()
        data = resp.json()
    try:
        parsed = _NewsResponse.model_validate(data)
    except ValidationError:
        return []
    out: list[NewsStory] = []
    for art in parsed.articles[:10]:
        if not art.title:
            continue
        out.append(
            NewsStory(
                title=art.title,
                description=art.description or "",
                url=art.url or "",
                source=art.source.name if art.source else "",
            )
        )
    return out
