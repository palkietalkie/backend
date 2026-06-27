import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.notifications.notification_kinds import STREAK_WARNING
from app.notifications.streak_warning import send_streak_warning as mod
from app.notifications.streak_warning.send_streak_warning import send_streak_warning
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo: 12:00 UTC == 21:00 local == STREAK_WARNING_HOUR_LOCAL.
_STREAK_WARNING = datetime(2026, 6, 24, 12, 0, tzinfo=UTC)


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        "tok-x",
    )


async def _add_session(db: DBConn, user_id: uuid.UUID, started_at: datetime) -> None:
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        started_at,
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


async def test_pushes_streak_warning_to_streak_holder_who_skipped_today(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 5)
    await _add_token(db, fake_user["id"])
    await _add_session(
        db, fake_user["id"], _STREAK_WARNING - timedelta(days=1)
    )  # practiced yesterday

    count = await send_streak_warning(db, _STREAK_WARNING)

    assert count == 1
    assert len(sent) == 1
    stamped = await db.fetchval(
        "SELECT per_kind_key FROM notification_log WHERE user_id = $1 AND kind = $2",
        fake_user["id"],
        STREAK_WARNING,
    )
    assert stamped is not None


async def test_skips_when_no_live_streak(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 0)  # no streak to lose
    await _add_token(db, fake_user["id"])
    await _add_session(db, fake_user["id"], _STREAK_WARNING - timedelta(days=1))

    assert await send_streak_warning(db, _STREAK_WARNING) == 0
    assert sent == []


async def test_skips_when_practiced_today(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 5)
    await _add_token(db, fake_user["id"])
    await _add_session(db, fake_user["id"], _STREAK_WARNING)  # session today (Tokyo) → streak safe

    assert await send_streak_warning(db, _STREAK_WARNING) == 0
    assert sent == []
