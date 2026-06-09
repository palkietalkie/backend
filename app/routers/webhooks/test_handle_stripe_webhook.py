"""Tests for POST /webhooks/stripe — signature verification + dispatch wiring."""

import hashlib
import hmac
import json
import time
import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

WEBHOOK_SECRET = "whsec_test_secret"


@pytest.fixture(autouse=True)
def force_test_webhook_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", WEBHOOK_SECRET)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _stripe_sig(payload: bytes) -> str:
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(WEBHOOK_SECRET.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _event(etype: str, **data: Any) -> dict[str, Any]:
    return {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "object": "event",
        "type": etype,
        "api_version": "2024-04-10",
        "created": int(time.time()),
        "data": {"object": data},
    }


async def test_webhook_400_on_missing_signature(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post("/webhooks/stripe", content=b"{}")
    assert resp.status_code == 400


async def test_webhook_400_on_bad_signature(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/webhooks/stripe",
        content=b"{}",
        headers={"Stripe-Signature": "t=1,v1=deadbeef"},
    )
    assert resp.status_code == 400


async def test_webhook_returns_reason_on_no_clerk_user(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    payload = json.dumps(_event("customer.subscription.updated", id="sub_1")).encode()
    sig = _stripe_sig(payload)
    resp = await client.post("/webhooks/stripe", content=payload, headers={"Stripe-Signature": sig})
    assert resp.status_code == 200
    assert resp.json()["reason"] == "no clerk_user_id in metadata"


async def test_webhook_applies_when_clerk_id_present(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    clerk_id = "user_stripe_webhook_under_test"
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        uuid.uuid4(),
        clerk_id,
    )
    payload = json.dumps(
        _event(
            "customer.subscription.updated",
            id="sub_x",
            status="active",
            current_period_end=int(time.time()) + 86400,
            cancel_at_period_end=False,
            metadata={"clerk_user_id": clerk_id},
        )
    ).encode()
    sig = _stripe_sig(payload)
    resp = await client.post("/webhooks/stripe", content=payload, headers={"Stripe-Signature": sig})
    assert resp.status_code == 200
    assert resp.json() == {"ok": "true"}
    row = await db.fetchrow("SELECT premium FROM users WHERE clerk_user_id = $1", clerk_id)
    assert row is not None
    assert row["premium"] is True
