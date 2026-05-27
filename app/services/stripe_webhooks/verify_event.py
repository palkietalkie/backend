from typing import Any

import stripe

from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError


def verify_event(
    *, payload: bytes, signature: str | None, secret: str
) -> dict[str, Any]:
    if not signature:
        raise InvalidSignatureError("missing Stripe-Signature header")
    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=signature, secret=secret
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise InvalidSignatureError(str(e)) from e
    # `stripe.Event` is dict-like via __getitem__ but doesn't support `dict(event)` cleanly. `_to_dict_recursive` is the SDK's private-but-stable serializer; `to_dict` only walks the top level and leaves nested objects as `StripeObject`.
    out = event._to_dict_recursive()
    assert isinstance(
        out, dict
    ), f"stripe event serializer returned {type(out).__name__}"
    return out
