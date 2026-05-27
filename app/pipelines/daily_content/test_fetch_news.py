"""fetch_news: NewsAPI client tests."""

import httpx
import pytest
import respx

from app.config import Settings
from app.pipelines.daily_content.fetch_news import fetch_news

NEWS_URL = "https://newsapi.org/v2/top-headlines"


@respx.mock
async def test_fetch_news_returns_empty_when_key_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert await fetch_news() == []
    finally:
        get_settings.cache_clear()


@respx.mock
async def test_fetch_news_parses_articles(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "test-news-key")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        respx.get(NEWS_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "articles": [
                        {
                            "title": "Big story",
                            "description": "what happened",
                            "url": "https://example.com/big",
                            "source": {"name": "Example"},
                        },
                        {"title": None, "description": "", "url": ""},
                    ]
                },
            )
        )
        out = await fetch_news()
    finally:
        get_settings.cache_clear()
    assert len(out) == 1
    assert out[0].title == "Big story"
    assert out[0].source == "Example"


@respx.mock
async def test_fetch_news_returns_empty_on_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "test-news-key")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        respx.get(NEWS_URL).mock(return_value=httpx.Response(200, json={"articles": "broken"}))
        out = await fetch_news()
    finally:
        get_settings.cache_clear()
    assert out == []
