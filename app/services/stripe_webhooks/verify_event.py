import json
from typing import Any

import stripe
from pydantic import TypeAdapter, ValidationError

from app.services.stripe_webhooks.invalid_signature_error import InvalidSignatureError

_DICT_ADAPTER: TypeAdapter[dict[str, Any]] = TypeAdapter(dict[str, Any])


def verify_event(*, payload: bytes, signature: str | None, secret: str) -> dict[str, Any]:
    if not signature:
        raise InvalidSignatureError("missing Stripe-Signature header")
    try:
        # Verified only for its side effect (signature check). We re-parse the payload ourselves so nested objects come back as plain dicts (the StripeObject tree's recursive-dict serializer is protected).
        # Stripe ships `py.typed` but their `_webhook.py:construct_event` carries no parameter annotations, so pyright reports the method as partially unknown. Suppress the warning at the only call site rather than reintroduce a local stripe stub that would shadow the SDK's real types.
        stripe.Webhook.construct_event(  # pyright: ignore[reportUnknownMemberType]
            payload=payload, sig_header=signature, secret=secret
        )
    except (ValueError, stripe.SignatureVerificationError) as e:
        raise InvalidSignatureError(str(e)) from e
    try:
        return _DICT_ADAPTER.validate_python(json.loads(payload))
    except (ValueError, ValidationError) as e:
        raise InvalidSignatureError(f"payload not a JSON object: {e}") from e
