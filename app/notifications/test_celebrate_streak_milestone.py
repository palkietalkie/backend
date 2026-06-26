import uuid

import pytest

from app.notifications import celebrate_streak_milestone as mod
from app.notifications.celebrate_streak_milestone import celebrate_streak_milestone
from app.notifications.notification_kinds import MILESTONE
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        "tok-x",
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


async def test_celebrates_a_new_milestone_and_records_it(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 7)
    await _add_token(db, fake_user["id"])

    assert await celebrate_streak_milestone(db, fake_user["id"]) is True
    assert len(sent) == 1
    recorded = await db.fetchval(
        "SELECT per_kind_key FROM notification_log WHERE user_id = $1 AND kind = $2",
        fake_user["id"],
        MILESTONE,
    )
    assert recorded == "7"


async def test_does_not_recelebrate_the_same_milestone(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 7)
    await _add_token(db, fake_user["id"])
    await db.execute(
        "INSERT INTO notification_log (user_id, kind, per_kind_key) VALUES ($1, $2, '7')",
        fake_user["id"],
        MILESTONE,
    )

    assert await celebrate_streak_milestone(db, fake_user["id"]) is False
    assert sent == []


async def test_non_milestone_streak_does_nothing(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 8)  # 8 isn't a milestone
    await _add_token(db, fake_user["id"])

    assert await celebrate_streak_milestone(db, fake_user["id"]) is False
    assert sent == []


async def test_respects_disabled_reminders(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    _fix_streak(monkeypatch, 7)
    await _add_token(db, fake_user["id"])
    await db.execute(
        "INSERT INTO notification_prefs (user_id, reminders_enabled) VALUES ($1, FALSE)",
        fake_user["id"],
    )

    assert await celebrate_streak_milestone(db, fake_user["id"]) is False
    assert sent == []
