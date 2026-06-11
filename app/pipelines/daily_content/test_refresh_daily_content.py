"""Tests for refresh_daily_content — runs the four-topic fetch+save pipeline."""

from datetime import UTC, datetime
from typing import Any

import pytest

from app.pipelines.daily_content import refresh_daily_content as mod
from app.pipelines.daily_content.models import TalkItem


async def test_refresh_daily_content_writes_all_topics(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake_news(category: str) -> list[TalkItem]:
        return [TalkItem(title=f"{category}-headline", summary="x", source="", image_url="")]

    async def _fake_quizzes(_seeds: list[str]) -> list[TalkItem]:
        return [TalkItem(title="q1", summary="a1", source="", image_url="")]

    saved: list[tuple[Any, str, list[TalkItem]]] = []

    async def _fake_save(day: object, topic: str, items: list[TalkItem], _db: object) -> None:
        saved.append((day, topic, items))

    class _Acquired:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _fake_pool() -> _Pool:
        return _Pool()

    monkeypatch.setattr(mod, "fetch_news_by_category", _fake_news)
    monkeypatch.setattr(mod, "generate_quizzes", _fake_quizzes)
    monkeypatch.setattr(mod, "save_topic_items", _fake_save)
    monkeypatch.setattr(mod, "get_neon_pool", _fake_pool)

    await mod.refresh_daily_content()

    topics = [t for _d, t, _i in saved]
    assert topics == ["politics", "business", "sports", "quizzes"]
    today = datetime.now(UTC).date()
    for d, _t, _i in saved:
        assert d == today
