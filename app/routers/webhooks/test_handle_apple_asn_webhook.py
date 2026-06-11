"""Tests for POST /webhooks/apple/asn — verifier and apply_decision are stubbed."""

from typing import Any

import pytest
from httpx import AsyncClient

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
