from enum import Enum


class SubscriptionTransition(Enum):
    """The user-facing subscription lifecycle moments that get a push. The ASN and Stripe handlers each map their own event vocabulary onto these, so the notification copy is written once, provider-agnostic. Silent moments (a normal renewal, a refund) simply don't map to a member."""

    WELCOME = "welcome"  # first/again subscribed: confirm the paid action
    PAYMENT_FAILED = "payment_failed"  # renewal charge failed, still in grace: actionable, prevents involuntary churn
    EXPIRED = "expired"  # lapsed to free: win-back
    CANCELED = "canceled"  # auto-renew turned off, premium until period end: retention
