from datetime import UTC, datetime

from app.services.apple_asn.constants import SOURCE
from app.services.neon.apply_subscription_state import apply_subscription_state
from app.services.neon.db_conn import DBConn


async def apply_decision(
    db: DBConn,
    *,
    clerk_user_id: str,
    decision: tuple[str, bool],
    expires_at: datetime | None,
    auto_renew: int | None,
) -> None:
    state, cancel_at_period_end = decision
    if state == "revoke":
        await apply_subscription_state(
            db,
            clerk_user_id,
            is_active=False,
            current_period_end=datetime.now(UTC),
            cancel_at_period_end=False,
            source=SOURCE,
        )
        return
    await apply_subscription_state(
        db,
        clerk_user_id,
        is_active=state == "active",
        current_period_end=expires_at,
        cancel_at_period_end=cancel_at_period_end or auto_renew == 0,
        source=SOURCE,
    )
