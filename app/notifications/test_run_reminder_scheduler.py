import asyncio

import pytest

from app.notifications import run_reminder_scheduler as mod


async def test_one_tick_runs_send_reminders(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"send": 0}

    async def _send(_db: object, _now: object) -> int:
        calls["send"] += 1
        # Stop the otherwise-infinite loop after the first tick.
        raise asyncio.CancelledError

    class _Acquired:
        async def __aenter__(self) -> object:
            return object()

        async def __aexit__(self, *_e: object) -> None:
            return None

    class _Pool:
        def acquire(self) -> _Acquired:
            return _Acquired()

    async def _pool() -> _Pool:
        return _Pool()

    async def _no_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr(mod, "send_reminders", _send)
    monkeypatch.setattr(mod, "get_neon_pool", _pool)
    monkeypatch.setattr(mod.asyncio, "sleep", _no_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_reminder_scheduler()
    assert calls["send"] == 1
