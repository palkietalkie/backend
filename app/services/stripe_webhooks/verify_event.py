import stripe

from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError


def verify_event(*, payload: bytes, signature: str | None, secret: str) -> stripe.Event:
    """Verify the signature and return Stripe's typed `Event`.

    Returns `stripe.Event` (not `dict[str, Any]`) so downstream code reads typed `event.data.object.metadata` instead of re-modeling the payload locally. `stripe.Webhook.construct_event` already does the JSON parse + signature verify + StripeObject construction in one step — we previously threw the StripeObject away and re-parsed via `json.loads`, which forced the rest of the pipeline to either Pydantic-shim the shape (broke on `customer: "cus_..."` strings) or fall back to plain dict access.
    """
    if not signature:
        raise InvalidSignatureError("missing Stripe-Signature header")
    try:
        # `construct_event` lacks parameter annotations in Stripe's `py.typed` package, so pyright reports the call as partially unknown. Suppress at the only call site rather than locally re-stubbing the SDK.
        return stripe.Webhook.construct_event(  # pyright: ignore[reportUnknownMemberType]
            payload=payload, sig_header=signature, secret=secret
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise InvalidSignatureError(str(e)) from e
