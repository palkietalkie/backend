"""Stripe webhook signature verification + dispatch tests.

Signature verification uses a real Stripe-style HMAC, computed inline to avoid mocking the Stripe SDK's verification routine. Dispatch is exercised against the postgres test container."""

import hashlib
import hmac
import json
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
import stripe

from app.services.neon.db_conn import DBConn
from app.services.stripe_webhooks.dispatch_event import dispatch_event
from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError
from app.services.stripe_webhooks.verify_event import verify_event

WEBHOOK_SECRET = "whsec_test_secret"


def _stripe_sig(payload: bytes, secret: str, ts: int | None = None) -> tuple[str, int]:
    ts = ts if ts is not None else int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}", ts


def build_event_dict(etype: str, **data: Any) -> dict[str, Any]:
    """Raw JSON-serializable event dict, for the HMAC-signing path in verify_event tests."""
    return {
        "id": f"evt_{uuid.uuid4().hex[:12]}",
        "object": "event",
        "type": etype,
        "api_version": "2024-04-10",
        "created": int(time.time()),
        "data": {"object": data},
    }


def build_stripe_event(etype: str, **data: Any) -> stripe.Event:
    """Typed `stripe.Event` matching what `verify_event` returns, for dispatch_event tests."""
    # type-escape: stripe — Event.construct_from is untyped in the SDK stubs, no typed constructor exists.
    return stripe.Event.construct_from(build_event_dict(etype, **data), key="sk_test")


def test_verify_event_happy_path() -> None:
    event = build_event_dict("customer.subscription.updated", id="sub_1")
    payload = json.dumps(event).encode()
    sig, _ = _stripe_sig(payload, WEBHOOK_SECRET)
    out = verify_event(payload=payload, signature=sig, secret=WEBHOOK_SECRET)
    assert out["type"] == "customer.subscription.updated"


def test_verify_event_missing_signature() -> None:
    with pytest.raises(InvalidSignatureError):
        verify_event(payload=b"{}", signature=None, secret=WEBHOOK_SECRET)


def test_verify_event_tampered_payload() -> None:
    event = build_event_dict("x")
    payload = json.dumps(event).encode()
    sig, _ = _stripe_sig(payload, WEBHOOK_SECRET)
    tampered = payload + b" "
    with pytest.raises(InvalidSignatureError):
        verify_event(payload=tampered, signature=sig, secret=WEBHOOK_SECRET)


def test_verify_event_wrong_secret() -> None:
    payload = b'{"id":"evt_1","type":"x","data":{"object":{}}}'
    sig, _ = _stripe_sig(payload, "whsec_OTHER")
    with pytest.raises(InvalidSignatureError):
        verify_event(payload=payload, signature=sig, secret=WEBHOOK_SECRET)


# extract_clerk_user_id has its own dedicated test file (test_extract_clerk_user_id.py) — kept there to colocate with the function and to cover the realistic Stripe-webhook shape (customer-as-string) the previous Pydantic shim broke.


@pytest.fixture
async def stripe_user(db: DBConn) -> dict[str, Any]:
    uid = uuid.uuid4()
    row = await db.fetchrow(
        """INSERT INTO users (id, clerk_user_id, premium)
           VALUES ($1, $2, FALSE)
           RETURNING id, clerk_user_id, premium, premium_ends_at""",
        uid,
        "user_stripe_under_test",
    )
    assert row is not None
    return dict(row)


async def test_dispatch_subscription_updated_active(
    db: DBConn, stripe_user: dict[str, Any]
) -> None:
    period_end = int((datetime.now(UTC) + timedelta(days=30)).timestamp())
    event = build_stripe_event(
        "customer.subscription.updated",
        id="sub_1",
        status="active",
        current_period_end=period_end,
        cancel_at_period_end=False,
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    out = await dispatch_event(db, event)
    assert out == "applied"
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", stripe_user["id"]
    )
    assert row is not None
    assert row["premium"] is True
    assert row["premium_ends_at"] is None


async def test_dispatch_subscription_cancel_at_period_end(
    db: DBConn, stripe_user: dict[str, Any]
) -> None:
    period_end_ts = int((datetime.now(UTC) + timedelta(days=10)).timestamp())
    event = build_stripe_event(
        "customer.subscription.updated",
        id="sub_1",
        status="active",
        current_period_end=period_end_ts,
        cancel_at_period_end=True,
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    await dispatch_event(db, event)
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", stripe_user["id"]
    )
    assert row is not None
    assert row["premium"] is True
    assert row["premium_ends_at"] is not None


async def test_dispatch_subscription_deleted(db: DBConn, stripe_user: dict[str, Any]) -> None:
    period_end_ts = int((datetime.now(UTC) + timedelta(days=5)).timestamp())
    event = build_stripe_event(
        "customer.subscription.deleted",
        id="sub_1",
        current_period_end=period_end_ts,
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    await dispatch_event(db, event)
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", stripe_user["id"]
    )
    assert row is not None
    assert row["premium"] is True
    assert row["premium_ends_at"] is not None


async def test_dispatch_charge_refunded_revokes_immediately(
    db: DBConn, stripe_user: dict[str, Any]
) -> None:
    await db.execute("UPDATE users SET premium = TRUE WHERE id = $1", stripe_user["id"])
    event = build_stripe_event(
        "charge.refunded",
        id="ch_1",
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    await dispatch_event(db, event)
    row = await db.fetchrow(
        "SELECT premium, premium_ends_at FROM users WHERE id = $1", stripe_user["id"]
    )
    assert row is not None
    assert row["premium"] is False
    assert row["premium_ends_at"] is not None


async def test_dispatch_logs_entitlement_change(db: DBConn, stripe_user: dict[str, Any]) -> None:
    event = build_stripe_event(
        "charge.refunded",
        id="ch_1",
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    await dispatch_event(db, event)
    rows = await db.fetch("SELECT event_type FROM events WHERE user_id = $1", stripe_user["id"])
    assert any(r["event_type"] == "entitlement_change" for r in rows)


async def test_dispatch_no_clerk_user_id(db: DBConn) -> None:
    event = build_stripe_event("customer.subscription.updated", id="sub_1")
    out = await dispatch_event(db, event)
    assert out == "no clerk_user_id in metadata"


async def test_dispatch_unhandled_event_type(db: DBConn, stripe_user: dict[str, Any]) -> None:
    event = build_stripe_event(
        "invoice.created",
        id="inv_1",
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    out = await dispatch_event(db, event)
    assert out.startswith("ignored ")


async def test_dispatch_payment_failed_triggers_notify(
    db: DBConn, stripe_user: dict[str, Any]
) -> None:
    # invoice.payment_failed is only the trigger for the "update your payment method" push (no state change; Stripe sets past_due via subscription.updated). With no device token, notify is a no-op, so this exercises the dispatch branch without a real APNs call.
    event = build_stripe_event(
        "invoice.payment_failed",
        id="inv_1",
        metadata={"clerk_user_id": stripe_user["clerk_user_id"]},
    )
    out = await dispatch_event(db, event)
    assert out == "notified payment_failed"
