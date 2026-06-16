import pytest

from app.daily_content import fetch_article_details as mod
from app.daily_content.fetch_article_details import fetch_article_details
from app.daily_content.models import TalkItem


def _item(title: str, url: str) -> TalkItem:
    return TalkItem(title=title, summary="blurb", source="AP", image_url="", url=url)


@pytest.mark.asyncio
async def test_fills_details_from_fetched_body(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_fetch(url: str, *, max_chars: int = 4000) -> str:
        return f"FULL BODY of {url}"

    monkeypatch.setattr(mod, "fetch_url_text", fake_fetch)
    out = await fetch_article_details(_item("A", "https://news.test/a"), 4000)
    assert out.details == "FULL BODY of https://news.test/a"
    # The original summary is untouched: details is additive depth, not a replacement.
    assert out.summary == "blurb"


@pytest.mark.asyncio
async def test_item_without_url_is_left_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_fetch(url: str, *, max_chars: int = 4000) -> str:
        raise AssertionError("should not fetch when there is no URL")

    monkeypatch.setattr(mod, "fetch_url_text", fail_fetch)
    out = await fetch_article_details(_item("Quiz", ""), 4000)
    assert out.details == ""


@pytest.mark.asyncio
async def test_failed_fetch_leaves_details_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    # fetch_url_text returns "" on any failure; the prompt then falls back to summary, so details must stay empty.
    async def empty_fetch(url: str, *, max_chars: int = 4000) -> str:
        return ""

    monkeypatch.setattr(mod, "fetch_url_text", empty_fetch)
    out = await fetch_article_details(_item("A", "https://news.test/down"), 4000)
    assert out.details == ""
