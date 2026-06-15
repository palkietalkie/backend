"""Tests for fetch_news_by_category — NewsAPI is mocked via respx."""

import httpx
import pytest
import respx

from app.daily_content.fetch_news_by_category import fetch_news_by_category

NEWS_URL = "https://newsapi.org/v2/top-headlines"


@respx.mock
async def test_fetch_news_by_category_returns_articles(monkeypatch: pytest.MonkeyPatch) -> None:
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
                            "title": "Senate passes Bill X",
                            "description": "60-40 vote.",
                            "urlToImage": "https://example.com/x.jpg",
                            "source": {"name": "AP"},
                        }
                    ]
                },
            )
        )
        items = await fetch_news_by_category("politics")
        assert len(items) == 1
        assert items[0].title == "Senate passes Bill X"
        assert items[0].source == "AP"
        assert items[0].image_url == "https://example.com/x.jpg"
    finally:
        get_settings.cache_clear()


@respx.mock
async def test_fetch_news_by_category_skips_articles_with_no_title(
    monkeypatch: pytest.MonkeyPatch,
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
                        {"title": None, "description": "nope"},
                        {"title": "Real", "description": "yes"},
                    ]
                },
            )
        )
        items = await fetch_news_by_category("politics")
        assert [i.title for i in items] == ["Real"]
    finally:
        get_settings.cache_clear()


async def test_fetch_news_by_category_empty_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert await fetch_news_by_category("politics") == []
    finally:
        get_settings.cache_clear()


@respx.mock
async def test_fetch_news_by_category_empty_on_malformed_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEWS_API_KEY", "test-news-key")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        respx.get(NEWS_URL).mock(return_value=httpx.Response(200, json={"unexpected": True}))
        items = await fetch_news_by_category("politics")
        # Validation passes (articles defaults to []) so we get an empty list.
        assert items == []
    finally:
        get_settings.cache_clear()
