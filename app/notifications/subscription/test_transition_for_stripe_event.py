from app.notifications.subscription.subscription_transition import SubscriptionTransition
from app.notifications.subscription.transition_for_stripe_event import transition_for_stripe_event


def test_created_active_is_welcome() -> None:
    assert (
        transition_for_stripe_event(
            "customer.subscription.created", is_active=True, cancel_at_period_end=False
        )
        == SubscriptionTransition.WELCOME
    )


def test_updated_with_cancel_is_canceled() -> None:
    assert (
        transition_for_stripe_event(
            "customer.subscription.updated", is_active=True, cancel_at_period_end=True
        )
        == SubscriptionTransition.CANCELED
    )


def test_payment_failed_is_payment_failed() -> None:
    assert (
        transition_for_stripe_event(
            "invoice.payment_failed", is_active=True, cancel_at_period_end=False
        )
        == SubscriptionTransition.PAYMENT_FAILED
    )


def test_silent_cases_map_to_none() -> None:
    # routine renewal / status sync (no cancel)
    assert (
        transition_for_stripe_event(
            "customer.subscription.updated", is_active=True, cancel_at_period_end=False
        )
        is None
    )
    # deleted: expiry is time-based, not notified here
    assert (
        transition_for_stripe_event(
            "customer.subscription.deleted", is_active=True, cancel_at_period_end=True
        )
        is None
    )
    assert (
        transition_for_stripe_event("charge.refunded", is_active=False, cancel_at_period_end=False)
        is None
    )
    # created but not active
    assert (
        transition_for_stripe_event(
            "customer.subscription.created", is_active=False, cancel_at_period_end=False
        )
        is None
    )
