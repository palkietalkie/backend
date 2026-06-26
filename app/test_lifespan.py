"""Lifespan tests — driver / stripe wiring + clean teardown of scheduler tasks."""

import asyncio
from typing import Any

import pytest
from fastapi import FastAPI

from app import lifespan as lifespan_mod


def test_schedulers_resolve_from_reorganized_modules() -> None:
    # After the pipelines → post_session_nlp / daily_content / audio_retention split, lifespan must import the schedulers from their new homes — not the deleted app.pipelines.* paths.
    from app.audio_retention.prune_expired_audio import run_prune_expired_audio_scheduler
    from app.daily_content.run_daily_content_scheduler import run_daily_content_scheduler
    from app.notifications.run_reminder_scheduler import run_reminder_scheduler

    assert lifespan_mod.run_daily_content_scheduler is run_daily_content_scheduler
    assert lifespan_mod.run_prune_expired_audio_scheduler is run_prune_expired_audio_scheduler
    assert lifespan_mod.run_reminder_scheduler is run_reminder_scheduler


async def test_lifespan_starts_and_cancels_scheduler_tasks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = {"daily": 0, "audio": 0, "reminder": 0}

    async def _daily() -> None:
        started["daily"] += 1
        while True:  # noqa: ASYNC110 — emulating a long-running scheduler task that's cancelled at teardown.
            await asyncio.sleep(3600)

    async def _audio() -> None:
        started["audio"] += 1
        while True:  # noqa: ASYNC110 — emulating a long-running scheduler task that's cancelled at teardown.
            await asyncio.sleep(3600)

    async def _reminder() -> None:
        started["reminder"] += 1
        while True:  # noqa: ASYNC110 — emulating a long-running scheduler task that's cancelled at teardown.
            await asyncio.sleep(3600)

    async def _close_driver() -> None:
        return None

    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    monkeypatch.setattr(lifespan_mod, "run_reminder_scheduler", _reminder)
    monkeypatch.setattr(lifespan_mod, "close_neo4j_driver", _close_driver)

    async with lifespan_mod.lifespan(FastAPI()):
        await asyncio.sleep(0)
        assert started == {"daily": 1, "audio": 1, "reminder": 1}


async def test_lifespan_warms_neo4j_driver_when_uri_remote(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("NEO4J_URI", "bolt://prod.neo4j.example.com:7687")
    from app.config import get_settings

    get_settings.cache_clear()
    called = {"get_neo4j_driver": 0}

    def _get_neo4j_driver() -> Any:
        called["get_neo4j_driver"] += 1
        return object()

    async def _close_driver() -> None:
        return None

    async def _daily() -> None:
        await asyncio.sleep(3600)

    async def _audio() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(lifespan_mod, "get_neo4j_driver", _get_neo4j_driver)
    monkeypatch.setattr(lifespan_mod, "close_neo4j_driver", _close_driver)
    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    try:
        async with lifespan_mod.lifespan(FastAPI()):
            await asyncio.sleep(0)
        assert called["get_neo4j_driver"] == 1
    finally:
        get_settings.cache_clear()


async def test_lifespan_does_not_warm_driver_for_localhost(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = {"get_neo4j_driver": 0}

    def _get_neo4j_driver() -> Any:
        called["get_neo4j_driver"] += 1
        return object()

    async def _close_driver() -> None:
        return None

    async def _daily() -> None:
        await asyncio.sleep(3600)

    async def _audio() -> None:
        await asyncio.sleep(3600)

    monkeypatch.setattr(lifespan_mod, "get_neo4j_driver", _get_neo4j_driver)
    monkeypatch.setattr(lifespan_mod, "close_neo4j_driver", _close_driver)
    monkeypatch.setattr(lifespan_mod, "run_daily_content_scheduler", _daily)
    monkeypatch.setattr(lifespan_mod, "run_prune_expired_audio_scheduler", _audio)
    async with lifespan_mod.lifespan(FastAPI()):
        await asyncio.sleep(0)
    assert called["get_neo4j_driver"] == 0
