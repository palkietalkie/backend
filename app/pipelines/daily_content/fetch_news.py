import httpx

from app.config import get_settings
from app.pipelines.daily_content.models import NewsStory


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
    out: list[NewsStory] = []
    for art in data.get("articles", [])[:10]:
        title = art.get("title")
        if not title:
            continue
        out.append(
            NewsStory(
                title=title,
                description=art.get("description") or "",
                url=art.get("url") or "",
                source=(art.get("source") or {}).get("name") or "",
            )
        )
    return out
