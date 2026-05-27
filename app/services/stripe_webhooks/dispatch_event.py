from datetime import UTC, datetime
from typing import Any

from app.services.neon.apply_subscription_state import apply_subscription_state
from app.services.neon.db_conn import DBConn
from app.services.stripe_webhooks.constants import ACTIVE_STATUSES, SOURCE
from app.services.stripe_webhooks.extract_clerk_user_id import extract_clerk_user_id
from app.services.stripe_webhooks.extract_period_end import extract_period_end


async def dispatch_event(db: DBConn, event: dict[str, Any]) -> str:
    etype = event["type"]
    data = event["data"]["object"]
    clerk_user_id = extract_clerk_user_id(data)
    if not clerk_user_id:
        return "no clerk_user_id in metadata"

    if etype in {"customer.subscription.created", "customer.subscription.updated"}:
        status_str = data.get("status")
        is_active = status_str in ACTIVE_STATUSES
        await apply_subscription_state(
            db,
            clerk_user_id,
            is_active=is_active,
            current_period_end=extract_period_end(data),
            cancel_at_period_end=bool(data.get("cancel_at_period_end")),
            source=SOURCE,
        )
        return "applied"
    if etype == "customer.subscription.deleted":
        # Remains active until period_end.
        await apply_subscription_state(
            db,
            clerk_user_id,
            is_active=True,
            current_period_end=extract_period_end(data, "ended_at"),
            cancel_at_period_end=True,
            source=SOURCE,
        )
        return "applied"
    if etype == "charge.refunded":
        await apply_subscription_state(
            db,
            clerk_user_id,
            is_active=False,
            current_period_end=datetime.now(UTC),
            cancel_at_period_end=False,
            source=SOURCE,
        )
        return "applied"
    return f"ignored {etype}"
