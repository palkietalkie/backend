import stripe


def extract_clerk_user_id(obj: stripe.StripeObject) -> str | None:
    """Pull `clerk_user_id` off a Stripe event's `data.object`.

    Reads from the subscription's `metadata.clerk_user_id` first (the path the iOS subscription-create flow uses), then falls back to the customer's `metadata.clerk_user_id` when `customer` is an expanded object. Real webhook payloads typically deliver `customer` as the string id `"cus_..."`; that's harmless — the second try-block trips `TypeError` when string-subscripting `"cus_..."["metadata"]` and we fall through to None.

    `stripe.StripeObject` is the typed payload Stripe's SDK returns from `Webhook.construct_event`. It supports `__getitem__` but NOT `.get()` (it doesn't subclass dict — has its own `_data` backing). Subscript + try/except is the idiomatic access pattern.
    """
    try:
        sub_id = obj["metadata"]["clerk_user_id"]
        if isinstance(sub_id, str) and sub_id:
            return sub_id
    except KeyError, TypeError:
        pass
    try:
        cust_id = obj["customer"]["metadata"]["clerk_user_id"]
        if isinstance(cust_id, str) and cust_id:
            return cust_id
    except KeyError, TypeError:
        pass
    return None
