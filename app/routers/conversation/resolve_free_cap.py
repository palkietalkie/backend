from typing import Literal

from fastapi import HTTPException, status

from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_this_week import sum_seconds_used_this_week
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today


async def resolve_free_cap(
    user: UserRow, db: DBConn
) -> tuple[int | None, Literal["daily", "weekly"] | None]:
    """Free-plan time check for a session start: (seconds left before a cap stops this session, which cap).

    (None, None) for premium — no cap, no countdown. For free users two windows apply (daily resets at user-local midnight, weekly at user-local Monday 00:00); if either is already spent this raises 402 so iOS shows the out-of-time screen instead of starting a session. Otherwise it returns how long until the tighter window stops them and which window that is, so iOS can wrap up ~30s early and, when the cap hits, say the right thing. On a tie it reports "weekly": both caps stop the user at once, but the weekly block lasts until Monday (worse than "back tomorrow"), so that's the message that must show.
    """
    if check_is_premium_now(user):
        return None, None
    used_today = await sum_seconds_used_today(user, db)
    if used_today >= FREE_MINUTES_PER_DAY * 60:
        # Structured detail (not a bare string) so iOS reads free_limit_kind to show the right limit screen, mirroring the 200 path's field, instead of string-sniffing the message.
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "free_limit_kind": "daily",
                "message": f"daily free limit reached ({FREE_MINUTES_PER_DAY} min). upgrade or come back at local midnight.",
            },
        )
    used_this_week = await sum_seconds_used_this_week(user, db)
    if used_this_week >= FREE_MINUTES_PER_WEEK * 60:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "free_limit_kind": "weekly",
                "message": f"weekly free limit reached ({FREE_MINUTES_PER_WEEK} min). upgrade or come back next Monday.",
            },
        )
    daily_remaining = FREE_MINUTES_PER_DAY * 60 - used_today
    weekly_remaining = FREE_MINUTES_PER_WEEK * 60 - used_this_week
    kind: Literal["daily", "weekly"] = "weekly" if weekly_remaining <= daily_remaining else "daily"
    return min(daily_remaining, weekly_remaining), kind
