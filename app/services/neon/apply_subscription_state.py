from datetime import UTC, datetime

from app.services.neon.db_conn import DBConn
from app.services.neon.find_user_by_clerk_id import find_user_by_clerk_id


async def apply_subscription_state(
    db: DBConn,
    clerk_user_id: str,
    *,
    is_active: bool,
    current_period_end: datetime | None,
    cancel_at_period_end: bool,
    source: str,
) -> None:
    # Cancel-at-period-end (Stripe) and the equivalent ASN ``DID_FAIL_TO_RENEW`` / ``DID_CHANGE_RENEWAL_STATUS=off`` keep the user premium until current_period_end. Refunds and explicit revokes flip premium=False immediately.
    # No-op silently if the user is unknown — Stripe / Apple may send webhooks for users who haven't completed Clerk onboarding yet.
    user = await find_user_by_clerk_id(db, clerk_user_id)
    if user is None:
        return
    if is_active:
        new_premium = True
        new_ends_at = current_period_end if cancel_at_period_end else None
    else:
        new_premium = False
        new_ends_at = current_period_end or datetime.now(UTC)

    async with db.transaction():
        await db.execute(
            """UPDATE users
               SET premium = $2, premium_ends_at = $3, updated_at = NOW()
               WHERE clerk_user_id = $1""",
            clerk_user_id,
            new_premium,
            new_ends_at,
        )
        await db.execute(
            """INSERT INTO events (user_id, event_type, ts, props)
               VALUES ($1, $2, $3, $4)""",
            user["id"],
            "entitlement_change",
            datetime.now(UTC),
            {
                "premium": new_premium,
                "premium_ends_at": new_ends_at.isoformat() if new_ends_at else None,
                "source": source,
            },
        )
