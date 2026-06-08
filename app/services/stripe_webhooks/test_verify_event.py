"""Stripe webhook signature verification. Wraps `stripe.Webhook.construct_event` to raise our own InvalidSignatureError on every failure mode (missing sig, bad sig, non-dict payload)."""

import json

import pytest
import stripe

from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError
from app.services.stripe_webhooks.verify_event import verify_event


def _stub_construct_event(monkeypatch: pytest.MonkeyPatch) -> None:
    # Replace the real signature verifier with a no-op so we control the failure modes from outside.
    def _noop(**_kwargs: object) -> None:
        return None

    monkeypatch.setattr(stripe.Webhook, "construct_event", _noop)


def test_raises_when_signature_header_missing() -> None:
    with pytest.raises(InvalidSignatureError, match="missing"):
        verify_event(payload=b'{"x": 1}', signature=None, secret="whsec_x")


def test_raises_when_stripe_signature_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(**_kwargs: object) -> None:
        raise stripe.SignatureVerificationError("bad sig", "sig_header")

    monkeypatch.setattr(stripe.Webhook, "construct_event", _boom)
    with pytest.raises(InvalidSignatureError, match="bad sig"):
        verify_event(payload=b'{"x": 1}', signature="t=1,v1=deadbeef", secret="whsec_x")


def test_raises_when_payload_is_not_json(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_construct_event(monkeypatch)
    with pytest.raises(InvalidSignatureError, match="not a JSON object"):
        verify_event(payload=b"not json at all", signature="t=1,v1=x", secret="whsec_x")


def test_raises_when_payload_is_not_a_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_construct_event(monkeypatch)
    with pytest.raises(InvalidSignatureError, match="not a JSON object"):
        verify_event(payload=b"[1,2,3]", signature="t=1,v1=x", secret="whsec_x")


def test_returns_parsed_dict_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    _stub_construct_event(monkeypatch)
    event = {"id": "evt_1", "type": "customer.subscription.updated"}
    result = verify_event(
        payload=json.dumps(event).encode(), signature="t=1,v1=x", secret="whsec_x"
    )
    assert result == event
