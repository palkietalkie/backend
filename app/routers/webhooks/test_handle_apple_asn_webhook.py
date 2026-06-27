"""Tests for POST /webhooks/apple/asn — verifier and apply_decision are stubbed."""

from typing import Any

import pytest
from httpx import AsyncClient

from app.notifications.subscription_transition import SubscriptionTransition
from app.routers.webhooks import handle_apple_asn_webhook as mod
from app.services.apple_asn._fakes import FakeVerifier, build_notification_dict
from app.services.apple_asn.exceptions import (
    AppleLibraryMissingError,
    InvalidSignatureError,
)
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_400_when_missing_signed_payload(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _get_verifier() -> Any:
        return object()

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={})
    assert resp.status_code == 400


async def test_503_when_apple_lib_missing(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _get_verifier() -> Any:
        raise AppleLibraryMissingError("not installed")

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 503


async def test_400_when_signature_invalid(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    async def _get_verifier() -> Any:
        return object()

    def _verify(_v: object, _p: str) -> tuple[object, str]:
        raise InvalidSignatureError("bad sig")

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    monkeypatch.setattr(mod, "verify_and_decode", _verify)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 400


async def test_no_app_account_token_returns_ok_with_reason(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    notif = build_notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(notification=notif, transaction={}, renewal={})

    async def _get_verifier() -> Any:
        return verifier

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 200
    assert resp.json()["reason"].startswith("no appAccountToken")


async def test_unhandled_notification_type_returns_ok_with_reason(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    notif = build_notification_dict(raw_type="UNKNOWN_TYPE_XYZ")
    verifier = FakeVerifier(
        notification=notif,
        transaction={"appAccountToken": "user_x"},
        renewal={},
    )

    async def _get_verifier() -> Any:
        return verifier

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 200
    assert resp.json()["reason"].startswith("unhandled")


async def test_applies_decision_on_known_notification(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Seed a user we can resolve via clerk_user_id.
    clerk_id = "user_apple_decision_under_test"
    user_id = await db.fetchval(
        """INSERT INTO users (id, clerk_user_id, premium)
           VALUES (gen_random_uuid(), $1, FALSE)
           RETURNING id""",
        clerk_id,
    )
    assert user_id is not None

    notif = build_notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(
        notification=notif,
        transaction={"appAccountToken": clerk_id, "expiresDate": 1_900_000_000_000},
        renewal={"autoRenewStatus": 1},
    )

    async def _get_verifier() -> Any:
        return verifier

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 200
    row = await db.fetchrow("SELECT premium FROM users WHERE clerk_user_id = $1", clerk_id)
    assert row is not None
    assert row["premium"] is True


async def test_subscribed_fires_the_welcome_notification(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clerk_id = "user_apple_welcome_under_test"
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES (gen_random_uuid(), $1, FALSE)",
        clerk_id,
    )
    captured: list[tuple[str, SubscriptionTransition]] = []

    async def _fake_notify(_db: object, cuid: str, transition: SubscriptionTransition) -> int:
        captured.append((cuid, transition))
        return 0

    monkeypatch.setattr(mod, "notify_subscription_change", _fake_notify)

    notif = build_notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(
        notification=notif,
        transaction={"appAccountToken": clerk_id, "expiresDate": 1_900_000_000_000},
        renewal={"autoRenewStatus": 1},
    )

    async def _get_verifier() -> Any:
        return verifier

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 200
    assert captured == [(clerk_id, SubscriptionTransition.WELCOME)]


async def test_slack_line_uses_human_label_not_raw_clerk_id(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The ASN Slack alert must read as a person, not a raw clerk id. With the user's name + email known, it shows "Taka <taka@...>".
    clerk_id = "user_apple_label_under_test"
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium, preferred_name, email)
           VALUES (gen_random_uuid(), $1, FALSE, $2, $3)""",
        clerk_id,
        "Taka",
        "taka@example.test",
    )
    posted: list[str] = []

    async def _fake_post(_channel: str, text: str, thread_ts: str | None = None) -> None:
        posted.append(text)

    async def _fake_notify(_db: object, _cuid: str, _t: SubscriptionTransition) -> int:
        return 0

    monkeypatch.setattr(mod, "post_message", _fake_post)
    monkeypatch.setattr(mod, "notify_subscription_change", _fake_notify)

    notif = build_notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(
        notification=notif,
        transaction={"appAccountToken": clerk_id, "expiresDate": 1_900_000_000_000},
        renewal={"autoRenewStatus": 1},
    )

    async def _get_verifier() -> Any:
        return verifier

    monkeypatch.setattr(mod, "get_verifier", _get_verifier)
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/apple/asn", json={"signedPayload": "abc"})
    assert resp.status_code == 200
    assert posted, "the webhook posts a Slack line"
    assert "Taka <taka@example.test>" in posted[0]
    assert clerk_id not in posted[0], "raw clerk id must not leak into the Slack line"
