import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.notifications import send_reminders as mod
from app.notifications.send_reminders import send_reminders
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo: 10:00 UTC == 19:00 local == default reminder hour.
_DUE = datetime(2026, 6, 24, 10, 0, tzinfo=UTC)


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


def _spy(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, LocalizedAlert]]:
    sent: list[tuple[str, LocalizedAlert]] = []

    async def _fake_send(token: str, alert: LocalizedAlert) -> PushResult:
        sent.append((token, alert))
        return PushResult(token=token, ok=True)

    monkeypatch.setattr(mod, "send_push", _fake_send)
    return sent


async def test_pushes_due_user_who_has_not_practiced_today_and_stamps(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy(monkeypatch)
    await _add_token(db, fake_user["id"])
    await _add_session(
        db, fake_user["id"], _DUE - timedelta(days=1)
    )  # practiced yesterday, not today

    count = await send_reminders(db, _DUE)

    assert count == 1
    assert len(sent) == 1
    # Stamped so the next hourly tick won't push them again today.
    stamped = await db.fetchval(
        "SELECT last_reminded_on FROM notification_prefs WHERE user_id = $1", fake_user["id"]
    )
    assert stamped is not None


async def test_skips_user_who_already_practiced_today(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy(monkeypatch)
    await _add_token(db, fake_user["id"])
    await _add_session(db, fake_user["id"], _DUE)  # a session today (Tokyo) → already showed up

    count = await send_reminders(db, _DUE)

    assert count == 0
    assert sent == []
