import pytest

from app.notifications.subscription.build_subscription_alert import build_subscription_alert
from app.notifications.subscription.subscription_transition import SubscriptionTransition


@pytest.mark.parametrize(
    ("transition", "title", "body"),
    [
        (SubscriptionTransition.WELCOME, "notif_sub_welcome_title", "notif_sub_welcome_body"),
        (
            SubscriptionTransition.PAYMENT_FAILED,
            "notif_sub_payment_failed_title",
            "notif_sub_payment_failed_body",
        ),
        (SubscriptionTransition.EXPIRED, "notif_sub_expired_title", "notif_sub_expired_body"),
        (SubscriptionTransition.CANCELED, "notif_sub_canceled_title", "notif_sub_canceled_body"),
    ],
)
def test_maps_each_transition_to_its_loc_keys(
    transition: SubscriptionTransition, title: str, body: str
) -> None:
    alert = build_subscription_alert(transition)
    assert alert.title_loc_key == title
    assert alert.body_loc_key == body
    assert alert.body_args == ()
