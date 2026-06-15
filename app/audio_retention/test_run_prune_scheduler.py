"""Tests for run_prune_expired_audio_scheduler — cover startup catch-up and the loop body."""

import asyncio

import pytest

from app.audio_retention import prune_expired_audio as mod


async def test_scheduler_runs_startup_catch_up_then_schedules_loop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"prune": 0}

    async def _prune(conn: object = None) -> int:
        calls["prune"] += 1
        return 0

    # Stop the loop right after the first scheduled sleep by raising CancelledError.
    async def _short_sleep(_seconds: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(mod, "prune_expired_audio_once", _prune)
    monkeypatch.setattr(mod.asyncio, "sleep", _short_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_prune_expired_audio_scheduler()

    assert calls["prune"] == 1


async def test_scheduler_swallows_startup_failure_and_continues(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    calls = {"prune": 0}

    async def _prune(conn: object = None) -> int:
        calls["prune"] += 1
        if calls["prune"] == 1:
            raise RuntimeError("startup boom")
        return 0

    async def _short_sleep(_seconds: float) -> None:
        raise asyncio.CancelledError

    monkeypatch.setattr(mod, "prune_expired_audio_once", _prune)
    monkeypatch.setattr(mod.asyncio, "sleep", _short_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_prune_expired_audio_scheduler()
    assert "session_audio prune startup catch-up failed" in caplog.text


async def test_prune_expired_audio_once_pool_path(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Conn:
        async def execute(self, _sql: str) -> str:
            return "DELETE 3"

    class _Acquired:
        async def __aenter__(self) -> _Conn:
            return _Conn()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _get_neon_pool() -> _Pool:
        return _Pool()

    monkeypatch.setattr(mod, "get_neon_pool", _get_neon_pool)
    deleted = await mod.prune_expired_audio_once()
    assert deleted == 3


async def test_prune_expired_audio_once_handles_unparseable_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Conn:
        async def execute(self, _sql: str) -> str:
            # No trailing number → ValueError when parsing.
            return "DELETE not-a-number"

    deleted = await mod.prune_expired_audio_once(_Conn())  # type: ignore[arg-type]
    assert deleted == 0
