import pytest
from fastapi import HTTPException

from app.routers.conversation import resolve_free_cap as mod
from app.routers.conversation.resolve_free_cap import resolve_free_cap
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

DAY = FREE_MINUTES_PER_DAY * 60
WEEK = FREE_MINUTES_PER_WEEK * 60


def _const(value: int):
    async def _f(_user: object, _db: object) -> int:
        return value

    return _f


def _always_premium(_user: UserRow) -> bool:
    return True


async def test_premium_has_no_cap(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "check_is_premium_now", _always_premium)
    assert await resolve_free_cap(fake_user, db) == (None, None)


async def test_fresh_user_daily_window_binds(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(0))
    monkeypatch.setattr(mod, "sum_seconds_used_this_week", _const(0))
    # Daily 600 is tighter than weekly 1800, so daily binds.
    assert await resolve_free_cap(fake_user, db) == (DAY, "daily")


async def test_daily_window_binds_when_today_nearly_spent(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(540))
    monkeypatch.setattr(mod, "sum_seconds_used_this_week", _const(540))
    assert await resolve_free_cap(fake_user, db) == (60, "daily")


async def test_weekly_window_binds_when_week_nearly_spent(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(0))
    monkeypatch.setattr(mod, "sum_seconds_used_this_week", _const(1700))
    # weekly_remaining 100 < daily_remaining 600, so weekly binds.
    assert await resolve_free_cap(fake_user, db) == (100, "weekly")


async def test_tie_reports_weekly(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(300))
    monkeypatch.setattr(mod, "sum_seconds_used_this_week", _const(1500))
    # Both leave exactly 300s; the longer (weekly) block is the one that must show.
    assert await resolve_free_cap(fake_user, db) == (300, "weekly")


async def test_daily_cap_exhausted_raises_402(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(DAY))
    with pytest.raises(HTTPException) as exc:
        await resolve_free_cap(fake_user, db)
    assert exc.value.status_code == 402
    assert "daily" in str(exc.value.detail).lower()


async def test_weekly_cap_exhausted_raises_402(
    fake_user: UserRow, db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Under the daily cap but the weekly window is spent.
    monkeypatch.setattr(mod, "sum_seconds_used_today", _const(0))
    monkeypatch.setattr(mod, "sum_seconds_used_this_week", _const(WEEK))
    with pytest.raises(HTTPException) as exc:
        await resolve_free_cap(fake_user, db)
    assert exc.value.status_code == 402
    assert "weekly" in str(exc.value.detail).lower()
