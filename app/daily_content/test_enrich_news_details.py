from dataclasses import replace

import pytest

from app.daily_content import enrich_news_details as mod
from app.daily_content.enrich_news_details import enrich_news_details
from app.daily_content.models import TalkItem


@pytest.mark.asyncio
async def test_enriches_every_item_preserving_order(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_one(item: TalkItem, max_chars: int) -> TalkItem:
        return replace(item, details=f"body:{item.title}")

    monkeypatch.setattr(mod, "fetch_article_details", fake_one)
    items = [
        TalkItem(title=t, summary="s", source="", image_url="", url="u") for t in ("A", "B", "C")
    ]
    out = await enrich_news_details(items)
    assert [i.details for i in out] == ["body:A", "body:B", "body:C"]
