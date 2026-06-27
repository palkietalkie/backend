import uuid
from datetime import UTC, date, datetime

import pytest

from app.notifications.daily_content import send_daily_content_nudge as mod
from app.notifications.daily_content.send_daily_content_nudge import send_daily_content_nudge
from app.notifications.notification_kinds import DAILY_CONTENT
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.push_result import PushResult
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

# fake_user is Asia/Tokyo. Tokyo 07:00 == 22:00 UTC the previous day.
_MORNING = datetime(2026, 6, 23, 22, 0, tzinfo=UTC)
_LOCAL_TODAY = "2026-06-24"
_HEADLINE = "Apple unveils its first foldable iPhone"


async def _add_token(db: DBConn, user_id: uuid.UUID) -> None:
    await db.execute(
        "INSERT INTO device_tokens (id, user_id, apns_token) VALUES ($1, $2, $3)",
        uuid.uuid4(),
        user_id,
        "tok-x",
    )


async def _add_content(db: DBConn, day: date, topic: str, items: list[dict[str, str]]) -> None:
    # Plain Python list: the jsonb codec json.dumps it (a string would double-encode).
    await db.execute(
        "INSERT INTO daily_content (day, topic, items) VALUES ($1, $2, $3)",
        day,
        topic,
        items,
    )


def _spy_push(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, LocalizedAlert]]:
    sent: list[tuple[str, LocalizedAlert]] = []

    async def _fake(token: str, alert: LocalizedAlert) -> PushResult:
        sent.append((token, alert))
        return PushResult(token=token, ok=True)

    monkeypatch.setattr(mod, "send_push", _fake)
    return sent


async def test_sends_with_todays_headline_and_stamps(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    await _add_token(db, fake_user["id"])
    await _add_content(db, date(2026, 6, 23), "politics", [{"title": _HEADLINE}])

    count = await send_daily_content_nudge(db, _MORNING)

    assert count == 1
    assert len(sent) == 1
    _, alert = sent[0]
    assert alert.body_loc_key == "notif_daily_content_body"
    assert alert.body_args == (_HEADLINE,)  # today's real headline, injected
    stamped = await db.fetchval(
        "SELECT per_kind_key FROM notification_log WHERE user_id = $1 AND kind = $2",
        fake_user["id"],
        DAILY_CONTENT,
    )
    assert stamped == _LOCAL_TODAY


async def test_no_content_sends_nothing(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    await _add_token(db, fake_user["id"])  # no daily_content rows

    assert await send_daily_content_nudge(db, _MORNING) == 0
    assert sent == []


async def test_quizzes_only_content_has_no_headline_so_sends_nothing(
    db: DBConn, fake_user: UserRow, monkeypatch: pytest.MonkeyPatch
) -> None:
    sent = _spy_push(monkeypatch)
    await _add_token(db, fake_user["id"])
    await _add_content(
        db, date(2026, 6, 23), "quizzes", [{"title": "A quiz"}]
    )  # excluded from headlines

    assert await send_daily_content_nudge(db, _MORNING) == 0
    assert sent == []
