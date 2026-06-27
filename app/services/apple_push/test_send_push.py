from typing import Any

import pytest
from aioapns import NotificationRequest

from app.services.apple_push import send_push as send_push_mod
from app.services.apple_push.localized_alert import LocalizedAlert
from app.services.apple_push.send_push import send_push


class _FakeResponse:
    def __init__(self, *, ok: bool, description: str = "") -> None:
        self.is_successful = ok
        self.description = description


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self._response = response
        self.sent_message: dict[str, Any] | None = None

    async def send_notification(self, request: NotificationRequest) -> _FakeResponse:
        self.sent_message = request.message
        return self._response


async def test_serializes_localized_alert_into_aps_loc_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _FakeClient(_FakeResponse(ok=True))
    monkeypatch.setattr(send_push_mod, "get_client", lambda: client)
    alert = LocalizedAlert(
        title_loc_key="notif_keep_streak_title",
        body_loc_key="notif_keep_streak_body",
        body_args=("5",),
    )

    result = await send_push("tok123", alert)

    assert result.ok
    assert result.token == "tok123"
    assert client.sent_message is not None
    assert client.sent_message["aps"]["alert"] == {
        "title-loc-key": "notif_keep_streak_title",
        "loc-key": "notif_keep_streak_body",
        "loc-args": ["5"],
    }


async def test_omits_loc_args_when_alert_has_none(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeClient(_FakeResponse(ok=True))
    monkeypatch.setattr(send_push_mod, "get_client", lambda: client)

    await send_push("tok", LocalizedAlert(title_loc_key="t", body_loc_key="b"))

    assert client.sent_message is not None
    assert "loc-args" not in client.sent_message["aps"]["alert"]


async def test_badge_set_only_when_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _FakeClient(_FakeResponse(ok=True))
    monkeypatch.setattr(send_push_mod, "get_client", lambda: client)
    alert = LocalizedAlert(title_loc_key="t", body_loc_key="b")

    # Default: no badge key (reminders don't badge).
    await send_push("tok", alert)
    assert client.sent_message is not None
    assert "badge" not in client.sent_message["aps"]

    # Provided: it lands on aps.badge.
    await send_push("tok", alert, badge=3)
    assert client.sent_message is not None
    assert client.sent_message["aps"]["badge"] == 3


async def test_reports_apns_failure_description(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        send_push_mod,
        "get_client",
        lambda: _FakeClient(_FakeResponse(ok=False, description="BadDeviceToken")),
    )

    result = await send_push("tok", LocalizedAlert(title_loc_key="t", body_loc_key="b"))

    assert not result.ok
    assert result.reason == "BadDeviceToken"
