from datetime import UTC, datetime

import stripe


def extract_period_end(obj: stripe.StripeObject, *fallback_keys: str) -> datetime | None:
    """Pull `current_period_end` (or a fallback key) off a Stripe `data.object`.

    `stripe.StripeObject` supports `__getitem__` but not `.get()` — subscript + try/except is the idiomatic access pattern (see extract_clerk_user_id for the same SDK gotcha).
    """
    for key in ("current_period_end", *fallback_keys):
        try:
            value = obj[key]
        except KeyError:
            continue
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(int(value), tz=UTC)
    return None
