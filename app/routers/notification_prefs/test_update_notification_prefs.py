import pytest
from httpx import AsyncClient

from app.routers.notification_prefs import update_notification_prefs as mod
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


def _spy_post(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    posted: list[str] = []

    async def _fake(_channel: str, text: str, thread_ts: str | None = None) -> None:
        posted.append(text)

    monkeypatch.setattr(mod, "post_message", _fake)
    return posted


async def test_put_creates_row_when_missing(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.put(
        "/notification-prefs", json={"reminders_enabled": True, "reminder_hour_local": 8}
    )
    assert resp.status_code == 200
    assert resp.json() == {"reminders_enabled": True, "reminder_hour_local": 8}
    row = await db.fetchrow(
        "SELECT reminders_enabled, reminder_hour_local FROM notification_prefs WHERE user_id = $1",
        user["id"],
    )
    assert row is not None
    assert row["reminders_enabled"] is True
    assert row["reminder_hour_local"] == 8


async def test_put_updates_existing_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await db.execute(
        "INSERT INTO notification_prefs (user_id, reminders_enabled, reminder_hour_local) VALUES ($1, TRUE, 19)",
        user["id"],
    )
    resp = await client.put(
        "/notification-prefs", json={"reminders_enabled": True, "reminder_hour_local": 7}
    )
    assert resp.json()["reminder_hour_local"] == 7


async def test_disabling_reminders_slacks_the_churn_signal(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    posted = _spy_post(monkeypatch)
    # No row yet => defaults enabled; turning off is the off-transition we want to see.
    resp = await client.put(
        "/notification-prefs", json={"reminders_enabled": False, "reminder_hour_local": 19}
    )
    assert resp.status_code == 200
    assert len(posted) == 1
    assert "notifications_off" in posted[0]


async def test_no_slack_when_reminders_stay_enabled(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    posted = _spy_post(monkeypatch)
    await client.put(
        "/notification-prefs", json={"reminders_enabled": True, "reminder_hour_local": 9}
    )
    assert posted == []


async def test_no_slack_when_already_disabled(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    client, user = app_with_overrides
    await db.execute(
        "INSERT INTO notification_prefs (user_id, reminders_enabled, reminder_hour_local) VALUES ($1, FALSE, 19)",
        user["id"],
    )
    posted = _spy_post(monkeypatch)
    await client.put(
        "/notification-prefs", json={"reminders_enabled": False, "reminder_hour_local": 19}
    )
    assert posted == [], "already-off → on→off transition didn't happen, so no churn ping"


async def test_hour_out_of_range_is_422(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.put(
        "/notification-prefs", json={"reminders_enabled": True, "reminder_hour_local": 24}
    )
    assert resp.status_code == 422
