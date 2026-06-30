from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.routers.entitlement.check_has_full_access import check_has_full_access
from app.routers.entitlement.check_is_in_trial import check_is_in_trial
from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.routers.entitlement.compute_trial_ends_at import compute_trial_ends_at
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_this_week import sum_seconds_used_this_week
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today

router = APIRouter(prefix="/entitlement", tags=["entitlement"])


class EntitlementResponse(BaseModel):
    # True only for a PAYING premium subscriber. A first-month trial user is NOT premium (trial_active carries that), so the app can tell "subscribed" apart from "on a free trial that will end".
    is_premium: bool
    # True while inside the first-month free trial: uncapped like premium but temporary. iOS reads this + trial_ends_at to message "your free month, ends <date>".
    trial_active: bool
    trial_ends_at: datetime | None
    free_minutes_remaining_today: int
    free_minutes_remaining_this_week: int
    # The caps themselves — single source of truth lives in `app/routers/entitlement/constants.py`. iOS reads them off the entitlement response so the SubscriptionView's "10 min/day, 30 min/week" copy stays in lockstep with whatever the backend enforces.
    free_minutes_per_day_cap: int
    free_minutes_per_week_cap: int
    premium_ends_at: datetime | None


@router.get("", response_model=EntitlementResponse)
async def fetch_entitlement(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> EntitlementResponse:
    trial_active = check_is_in_trial(user)
    trial_ends_at = compute_trial_ends_at(user) if trial_active else None
    # Full access (paying premium OR inside the free trial) reports the caps as fully available — no DB count, no countdown. is_premium stays false for a trial-only user so the app can distinguish the two.
    if check_has_full_access(user):
        return EntitlementResponse(
            is_premium=check_is_premium_now(user),
            trial_active=trial_active,
            trial_ends_at=trial_ends_at,
            free_minutes_remaining_today=FREE_MINUTES_PER_DAY,
            free_minutes_remaining_this_week=FREE_MINUTES_PER_WEEK,
            free_minutes_per_day_cap=FREE_MINUTES_PER_DAY,
            free_minutes_per_week_cap=FREE_MINUTES_PER_WEEK,
            premium_ends_at=user["premium_ends_at"],
        )
    used_today_minutes = await sum_seconds_used_today(user, db) // 60
    used_week_minutes = await sum_seconds_used_this_week(user, db) // 60
    return EntitlementResponse(
        is_premium=False,
        trial_active=False,
        trial_ends_at=None,
        free_minutes_remaining_today=max(FREE_MINUTES_PER_DAY - used_today_minutes, 0),
        free_minutes_remaining_this_week=max(FREE_MINUTES_PER_WEEK - used_week_minutes, 0),
        free_minutes_per_day_cap=FREE_MINUTES_PER_DAY,
        free_minutes_per_week_cap=FREE_MINUTES_PER_WEEK,
        premium_ends_at=user["premium_ends_at"],
    )
