from app.notifications.subscription_transition import SubscriptionTransition


def transition_for_stripe_event(
    etype: str, *, is_active: bool, cancel_at_period_end: bool
) -> SubscriptionTransition | None:
    """Which subscription notification a Stripe event maps to, or None to stay silent.

    EXPIRED is intentionally NOT mapped here: on Stripe the actual lapse is time-based (premium_ends_at passing), not a webhook, and `subscription.deleted` keeps the user premium until period end, so firing "your Premium ended" then would be premature. Web win-back on true expiry is a separate (scheduled) concern; iOS expiry is covered by the ASN EXPIRED event."""
    if etype == "invoice.payment_failed":
        return SubscriptionTransition.PAYMENT_FAILED
    if etype == "customer.subscription.created" and is_active:
        return SubscriptionTransition.WELCOME
    if etype == "customer.subscription.updated" and cancel_at_period_end:
        return SubscriptionTransition.CANCELED
    return None
