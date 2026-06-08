"""Pin the realistic-Stripe-payload behavior of `extract_clerk_user_id`.

Before the 2026-06-08 fix, the function declared `customer: _Customer | None` on a Pydantic shim. Real Stripe webhook payloads send `data.object.customer` as a string customer id (not an expanded object), pydantic raised ValidationError on the whole payload, and the function returned None — which the dispatch_event handler logged as `"no clerk_user_id in metadata"` and skipped the `apply_subscription_state` write. The result: `premium=true` never flipped on real subscriptions, only on the unit tests that happened to omit the `customer` field entirely. This regression burned the live sandbox test for an entire afternoon.
"""

import stripe

from app.services.stripe_webhooks.extract_clerk_user_id import extract_clerk_user_id


def _stripe_object(data: dict[str, object]) -> stripe.StripeObject:
    # Mirrors what `stripe.Webhook.construct_event` returns for `data.object`. `construct_from` lacks parameter annotations in the SDK; ignore the unknown-member-type warning here.
    return stripe.StripeObject.construct_from(data, key="sk_test")  # pyright: ignore[reportUnknownMemberType]


def test_returns_subscription_metadata_when_customer_is_a_string_id() -> None:
    """The real Stripe-webhook shape: `customer` is `"cus_..."`, not an expanded dict."""
    obj = _stripe_object(
        {
            "id": "sub_test",
            "metadata": {"clerk_user_id": "user_abc"},
            "customer": "cus_test_id",
            "status": "active",
        }
    )
    assert extract_clerk_user_id(obj) == "user_abc"


def test_falls_back_to_expanded_customer_metadata() -> None:
    """When the caller asks for an expanded customer object, the clerk id may live on the customer instead of the subscription."""
    obj = _stripe_object(
        {
            "id": "sub_test",
            "metadata": {},
            "customer": {"id": "cus_test", "metadata": {"clerk_user_id": "user_xyz"}},
        }
    )
    assert extract_clerk_user_id(obj) == "user_xyz"


def test_subscription_metadata_wins_over_customer_metadata() -> None:
    """If both are present, the subscription's id is authoritative — the dispatch flow keys on the subscription event."""
    obj = _stripe_object(
        {
            "metadata": {"clerk_user_id": "sub_id"},
            "customer": {"metadata": {"clerk_user_id": "cust_id"}},
        }
    )
    assert extract_clerk_user_id(obj) == "sub_id"


def test_returns_none_when_neither_payload_carries_id() -> None:
    obj = _stripe_object({"metadata": {}, "customer": "cus_test"})
    assert extract_clerk_user_id(obj) is None


def test_returns_none_on_completely_empty_payload() -> None:
    assert extract_clerk_user_id(_stripe_object({})) is None


def test_handles_missing_customer_key_entirely() -> None:
    """Some Stripe event types omit `customer` altogether (e.g. `charge.refunded` on legacy data). Falls through to None."""
    obj = _stripe_object({"id": "evt_test", "metadata": {}})
    assert extract_clerk_user_id(obj) is None
