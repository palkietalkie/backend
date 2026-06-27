from app.notifications.subscription_transition import SubscriptionTransition
from app.notifications.transition_for_apple_notification import transition_for_apple_notification


def test_maps_lifecycle_types() -> None:
    assert transition_for_apple_notification("SUBSCRIBED") == SubscriptionTransition.WELCOME
    assert (
        transition_for_apple_notification("DID_FAIL_TO_RENEW")
        == SubscriptionTransition.PAYMENT_FAILED
    )
    assert transition_for_apple_notification("EXPIRED") == SubscriptionTransition.EXPIRED
    assert (
        transition_for_apple_notification("DID_CHANGE_RENEWAL_STATUS")
        == SubscriptionTransition.CANCELED
    )


def test_silent_types_map_to_none() -> None:
    for raw_type in ("DID_RENEW", "REFUND", "REVOKE", "SOMETHING_ELSE"):
        assert transition_for_apple_notification(raw_type) is None
