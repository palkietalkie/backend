from app.notifications.subscription.subscription_transition import SubscriptionTransition


def test_has_the_four_user_facing_transitions() -> None:
    assert {t.value for t in SubscriptionTransition} == {
        "welcome",
        "payment_failed",
        "expired",
        "canceled",
    }
