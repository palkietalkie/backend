from app.notifications.subscription.subscription_transition import SubscriptionTransition
from app.services.apple_push.localized_alert import LocalizedAlert

_KEYS: dict[SubscriptionTransition, tuple[str, str]] = {
    SubscriptionTransition.WELCOME: ("notif_sub_welcome_title", "notif_sub_welcome_body"),
    SubscriptionTransition.PAYMENT_FAILED: (
        "notif_sub_payment_failed_title",
        "notif_sub_payment_failed_body",
    ),
    SubscriptionTransition.EXPIRED: ("notif_sub_expired_title", "notif_sub_expired_body"),
    SubscriptionTransition.CANCELED: ("notif_sub_canceled_title", "notif_sub_canceled_body"),
}


def build_subscription_alert(transition: SubscriptionTransition) -> LocalizedAlert:
    """The localized push for a subscription-lifecycle moment. Static copy, no args (no per-user values that vary), so the device renders it in the user's language at delivery."""
    title, body = _KEYS[transition]
    return LocalizedAlert(title_loc_key=title, body_loc_key=body)
