import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.notifications.notification_kinds import WEEKLY_RECAP
from app.notifications.weekly_recap import send_weekly_recap as mod
from app.notifications.weekly_recap.send_weekly_recap import send_weekly_recap
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo. 2026-06-28 Sunday, Tokyo 18:00 == 09:00 UTC == recap moment; ISO week 2026-W26.
_RECAP = datetime(2026, 6, 28, 9, 0, tzinfo=UTC)
_ISO_WEEK = "2026-W26"


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        "tok-x",
    )


async def _add_session(
    db: DBConn, user_id: uuid.UUID, started_at: datetime, duration_seconds: int
) -> None:
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds) VALUES ($1, $2, $3, $4)",
        uuid.uuid4(),
        user_id,
        started_at,
        duration_seconds,
    )


def _spy_push(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, LocalizedAlert]]:
    sent: list[tuple[str, LocalizedAlert]] = []

    async def _fake(token: str, alert: LocalizedAlert) -> PushResult:
        sent.append((token, alert))
        return PushResult(token=token, ok=True)

    monkeypatch.setattr(mod, "send_push", _fake)
    return sent


def _fix_streak(monkeypatch: pytest.MonkeyPatch, value: int) -> None:
    async def _fake(_db: object, _uid: object) -> int:
        return value

    monkeypatch.setattr(mod, "compute_day_streak", _fake)


async def test_pushes_recap_with_sessions_minutes_and_streak(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 7)
    await _add_token(db, fake_user["id"])
    for d in (1, 2, 3):
        await _add_session(db, fake_user["id"], _RECAP - timedelta(days=d), 600)  # 3×10min = 30min

    count = await send_weekly_recap(db, _RECAP)

    assert count == 1
    _, alert = sent[0]
    assert alert.body_loc_key == "notif_weekly_recap_body_other"
    assert alert.body_args == ("3", "30", "7")  # sessions, minutes, streak (all numerals)
    stamped = await db.fetchval(
        "SELECT per_kind_key FROM notification_log WHERE user_id = $1 AND kind = $2",
        fake_user["id"],
        WEEKLY_RECAP,
    )
    assert stamped == _ISO_WEEK


async def test_sub_minute_session_floors_minutes_to_one_not_zero(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 5)
    await _add_token(db, fake_user["id"])
    await _add_session(db, fake_user["id"], _RECAP - timedelta(days=1), 20)  # 20s, would round to 0

    assert await send_weekly_recap(db, _RECAP) == 1
    _, alert = sent[0]
    assert alert.body_loc_key == "notif_weekly_recap_body_one"
    assert alert.body_args == ("1", "1", "5")  # sessions, minutes floored to 1, streak 5


async def test_zero_streak_with_activity_drops_streak_clause(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 0)  # practiced earlier in the week, streak already broken
    await _add_token(db, fake_user["id"])
    for d in (2, 3):
        await _add_session(db, fake_user["id"], _RECAP - timedelta(days=d), 600)  # 2×10min = 20min

    assert await send_weekly_recap(db, _RECAP) == 1
    _, alert = sent[0]
    assert alert.body_loc_key == "notif_weekly_recap_body_other_no_streak"
    assert alert.body_args == ("2", "20")  # sessions, minutes, no streak


async def test_skips_user_with_zero_sessions_this_week(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 0)
    await _add_token(db, fake_user["id"])
    await _add_session(
        db, fake_user["id"], _RECAP - timedelta(days=10), 600
    )  # outside 7-day window

    assert await send_weekly_recap(db, _RECAP) == 0
    assert sent == []
    stamped = await db.fetchval(
        "SELECT count(*) FROM notification_log WHERE user_id = $1 AND kind = $2",
        fake_user["id"],
        WEEKLY_RECAP,
    )
    assert stamped == 0
