"""Tests for run_daily_content_scheduler — cover the startup catch-up branch."""

import asyncio

import pytest

from app.pipelines.daily_content import run_daily_content_scheduler as mod
from app.pipelines.daily_content.models import TalkItem


async def test_scheduler_skips_refresh_when_all_topics_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"refresh": 0, "load": 0}
    full = {
        "politics": [TalkItem(title="t", summary="s", source="", image_url="")],
        "business": [TalkItem(title="t", summary="s", source="", image_url="")],
        "sports": [TalkItem(title="t", summary="s", source="", image_url="")],
        "quizzes": [TalkItem(title="t", summary="s", source="", image_url="")],
    }

    async def _load(_db: object) -> dict[str, list[TalkItem]]:
        calls["load"] += 1
        return full

    async def _refresh() -> None:
        calls["refresh"] += 1

    class _Acquired:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _get_pool() -> _Pool:
        return _Pool()

    async def _short_sleep(_s: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(mod, "load_today_topics", _load)
    monkeypatch.setattr(mod, "refresh_daily_content", _refresh)
    monkeypatch.setattr(mod, "get_pool", _get_pool)
    monkeypatch.setattr(mod.asyncio, "sleep", _short_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_daily_content_scheduler()

    assert calls["load"] == 1
    assert calls["refresh"] == 0


async def test_scheduler_refreshes_when_some_topics_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"refresh": 0}

    async def _load(_db: object) -> dict[str, list[TalkItem]]:
        return {"politics": [TalkItem(title="t", summary="s", source="", image_url="")]}

    async def _refresh() -> None:
        calls["refresh"] += 1

    class _Acquired:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _get_pool() -> _Pool:
        return _Pool()

    async def _short_sleep(_s: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(mod, "load_today_topics", _load)
    monkeypatch.setattr(mod, "refresh_daily_content", _refresh)
    monkeypatch.setattr(mod, "get_pool", _get_pool)
    monkeypatch.setattr(mod.asyncio, "sleep", _short_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_daily_content_scheduler()

    assert calls["refresh"] == 1


async def test_scheduler_swallows_startup_failure(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    async def _load_fails(_db: object) -> dict[str, list[TalkItem]]:
        raise RuntimeError("db down")

    async def _refresh() -> None:
        return None

    class _Acquired:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _get_pool() -> _Pool:
        return _Pool()

    async def _short_sleep(_s: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(mod, "load_today_topics", _load_fails)
    monkeypatch.setattr(mod, "refresh_daily_content", _refresh)
    monkeypatch.setattr(mod, "get_pool", _get_pool)
    monkeypatch.setattr(mod.asyncio, "sleep", _short_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_daily_content_scheduler()
    assert "daily_content startup catch-up failed" in caplog.text
