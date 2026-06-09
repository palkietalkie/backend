"""Stripe webhook signature verification. Wraps `stripe.Webhook.construct_event` to raise our own InvalidSignatureError on signature failure modes and otherwise return Stripe's typed `Event`."""

import pytest
import stripe

from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError
from app.services.stripe_webhooks.verify_event import verify_event


def test_raises_when_signature_header_missing() -> None:
    with pytest.raises(InvalidSignatureError, match="missing"):
        verify_event(payload=b'{"x": 1}', signature=None, secret="whsec_x")


def test_raises_when_stripe_signature_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(**_kwargs: object) -> None:
        raise stripe.SignatureVerificationError("bad sig", "sig_header")

    monkeypatch.setattr(stripe.Webhook, "construct_event", _boom)
    with pytest.raises(InvalidSignatureError, match="bad sig"):
        verify_event(payload=b'{"x": 1}', signature="t=1,v1=deadbeef", secret="whsec_x")


def test_returns_stripe_event_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """When construct_event succeeds, verify_event passes its typed `stripe.Event` straight through. Reading typed `.type` / `.data.object` downstream keeps us off the Pydantic-shim path that previously dropped real webhook payloads where `customer` was a string id."""
    event = stripe.Event.construct_from(  # pyright: ignore[reportUnknownMemberType]
        {"id": "evt_1", "type": "customer.subscription.updated", "data": {"object": {}}},
        key="sk_test",
    )

    def _ok(**_kwargs: object) -> stripe.Event:
        return event

    monkeypatch.setattr(stripe.Webhook, "construct_event", _ok)
    result = verify_event(payload=b"{}", signature="t=1,v1=x", secret="whsec_x")
    assert result is event
    assert result["type"] == "customer.subscription.updated"


def test_raises_when_construct_event_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stripe's construct_event raises ValueError on malformed JSON payloads; we surface that as InvalidSignatureError too so the router responds with 400."""

    def _value_err(**_kwargs: object) -> None:
        raise ValueError("not json")

    monkeypatch.setattr(stripe.Webhook, "construct_event", _value_err)
    with pytest.raises(InvalidSignatureError, match="not json"):
        verify_event(payload=b"garbage", signature="t=1,v1=x", secret="whsec_x")
