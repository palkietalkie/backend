import logging
from datetime import UTC, datetime

import stripe

from app.services.neon.apply_subscription_state import apply_subscription_state
from app.services.neon.db_conn import DBConn
from app.services.neon.find_user_by_clerk_id import find_user_by_clerk_id
from app.services.stripe_webhooks.constants import ACTIVE_STATUSES, SOURCE
from app.services.stripe_webhooks.extract_clerk_user_id import extract_clerk_user_id
from app.services.stripe_webhooks.extract_period_end import extract_period_end

_logger = logging.getLogger(__name__)


async def dispatch_event(db: DBConn, event: stripe.Event) -> str:
    etype = event["type"]
    data = event["data"]["object"]
    clerk_user_id = extract_clerk_user_id(data)
    _logger.info("stripe_dispatch etype=%s clerk_user_id=%s", etype, clerk_user_id)
    if clerk_user_id:
        existing = await find_user_by_clerk_id(db, clerk_user_id)
        _logger.info("stripe_dispatch user_lookup found=%s", existing is not None)
    if not clerk_user_id:
        return "no clerk_user_id in metadata"

    if etype in {"customer.subscription.created", "customer.subscription.updated"}:
        # StripeObject lacks `.get()`; subscript with try/except is the SDK-idiomatic access pattern.
        try:
            status_str = data["status"]
        except KeyError:
            status_str = None
        is_active = status_str in ACTIVE_STATUSES
        try:
            cancel_at_period_end = bool(data["cancel_at_period_end"])
        except KeyError:
            cancel_at_period_end = False
        await apply_subscription_state(
            db,
            clerk_user_id,
            is_active=is_active,
            current_period_end=extract_period_end(data),
            cancel_at_period_end=cancel_at_period_end,
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
