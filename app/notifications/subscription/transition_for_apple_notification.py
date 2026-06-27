from app.notifications.subscription.subscription_transition import SubscriptionTransition

# Apple ASN wire type -> the user-facing transition. DID_CHANGE_RENEWAL_STATUS maps to CANCELED to match the existing entitlement logic, which already treats it as cancel-at-period-end (constants.py).
_APPLE_TO_TRANSITION: dict[str, SubscriptionTransition] = {
    "SUBSCRIBED": SubscriptionTransition.WELCOME,
    "DID_FAIL_TO_RENEW": SubscriptionTransition.PAYMENT_FAILED,
    "EXPIRED": SubscriptionTransition.EXPIRED,
    "DID_CHANGE_RENEWAL_STATUS": SubscriptionTransition.CANCELED,
}


def transition_for_apple_notification(raw_type: str) -> SubscriptionTransition | None:
    """Which subscription notification an Apple ASN type maps to, or None to stay silent (DID_RENEW is a routine renewal; REFUND / REVOKE get no user-facing push)."""
    return _APPLE_TO_TRANSITION.get(raw_type)
