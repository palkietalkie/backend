from app.notifications.build_subscription_alert import build_subscription_alert
from app.notifications.subscription_transition import SubscriptionTransition
from app.services.apple_push.send_push import send_push
from app.services.neon.db_conn import DBConn


async def notify_subscription_change(
    db: DBConn, clerk_user_id: str, transition: SubscriptionTransition
) -> int:
    """Push the subscription-lifecycle notification for `transition` to all of the user's devices. Returns how many tokens were pushed.

    Called by the ASN and Stripe webhook handlers AFTER the entitlement state is written, so a push failure can never block the billing update. Looked up by clerk_user_id (the id both webhooks carry); a user with no device token gets nothing. Silent moments (a normal renewal, a refund) never reach here, the handler maps them to None and skips the call."""
    tokens = await db.fetch(
        """SELECT d.apns_token
             FROM device_tokens d
             JOIN users u ON u.id = d.user_id
            WHERE u.clerk_user_id = $1""",
        clerk_user_id,
    )
    if not tokens:
        return 0
    alert = build_subscription_alert(transition)
    for row in tokens:
        await send_push(row["apns_token"], alert)
    return len(tokens)
