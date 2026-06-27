import asyncio

import pytest

from app.notifications import run_reminder_scheduler as mod


def test_scheduler_holds_the_real_per_kind_senders() -> None:
    # The scheduler ticks every kind; lock that it imports each real sender from its per-kind home, so a wrong or broken import can't silently skip a notification kind.
    from app.notifications.daily_content.send_daily_content_nudge import send_daily_content_nudge
    from app.notifications.reminder.send_reminders import send_reminders
    from app.notifications.streak_warning.send_streak_warning import send_streak_warning
    from app.notifications.weekly_recap.send_weekly_recap import send_weekly_recap

    assert mod.send_reminders is send_reminders
    assert mod.send_streak_warning is send_streak_warning
    assert mod.send_weekly_recap is send_weekly_recap
    assert mod.send_daily_content_nudge is send_daily_content_nudge


async def test_one_tick_runs_both_daily_and_streak_warning_passes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = {"daily": 0, "streak_warning": 0}

    async def _daily(_db: object, _now: object) -> int:
        calls["daily"] += 1
        return 0

    async def _streak_warning(_db: object, _now: object) -> int:
        calls["streak_warning"] += 1
        # Stop the otherwise-infinite loop after the first full tick (both passes ran).
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

    monkeypatch.setattr(mod, "send_reminders", _daily)
    monkeypatch.setattr(mod, "send_streak_warning", _streak_warning)
    monkeypatch.setattr(mod, "get_neon_pool", _pool)
    monkeypatch.setattr(mod.asyncio, "sleep", _no_sleep)

    with pytest.raises(asyncio.CancelledError):
        await mod.run_reminder_scheduler()
    assert calls == {"daily": 1, "streak_warning": 1}
