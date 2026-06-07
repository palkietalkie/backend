"""Lifespan tests — driver / stripe wiring + clean teardown of scheduler tasks."""

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI

from app import lifespan as lifespan_mod


async def test_lifespan_starts_and_cancels_scheduler_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = {"daily": 0, "audio": 0}

    async def _daily() -> None:
        started["daily"] += 1
        while True:  # noqa: ASYNC110 — emulating a long-running scheduler task that's cancelled at teardown.
            await asyncio.sleep(3600)

    async def _audio() -> None:
        started["audio"] += 1
        while True:  # noqa: ASYNC110 — emulating a long-running scheduler task that's cancelled at teardown.
            await asyncio.sleep(3600)

    async def _close_driver() -> None:
        return None

    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    monkeypatch.setattr(lifespan_mod, "close_driver", _close_driver)

    async with lifespan_mod.lifespan(FastAPI()):
        await asyncio.sleep(0)
        assert started == {"daily": 1, "audio": 1}


async def test_lifespan_warms_neo4j_driver_when_uri_remote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEO4J_URI", "bolt://prod.neo4j.example.com:7687")
    from app.config import get_settings

    get_settings.cache_clear()
    called = {"get_driver": 0}

    def _get_driver() -> Any:
        called["get_driver"] += 1
        return object()

    async def _close_driver() -> None:
        return None

    async def _daily() -> None:
        await asyncio.sleep(3600)

    async def _audio() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(lifespan_mod, "get_driver", _get_driver)
    monkeypatch.setattr(lifespan_mod, "close_driver", _close_driver)
    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    try:
        async with lifespan_mod.lifespan(FastAPI()):
            await asyncio.sleep(0)
        assert called["get_driver"] == 1
    finally:
        get_settings.cache_clear()


async def test_lifespan_does_not_warm_driver_for_localhost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"get_driver": 0}

    def _get_driver() -> Any:
        called["get_driver"] += 1
        return object()

    async def _close_driver() -> None:
        return None

    async def _daily() -> None:
        await asyncio.sleep(3600)

    async def _audio() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(lifespan_mod, "get_driver", _get_driver)
    monkeypatch.setattr(lifespan_mod, "close_driver", _close_driver)
    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    async with lifespan_mod.lifespan(FastAPI()):
        await asyncio.sleep(0)
    assert called["get_driver"] == 0
