from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_this_week import sum_seconds_used_this_week
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today

router = APIRouter(prefix="/entitlement", tags=["entitlement"])


class EntitlementResponse(BaseModel):
    is_premium: bool
    free_minutes_remaining_today: int
    free_minutes_remaining_this_week: int
    # The caps themselves — single source of truth lives in `app/routers/entitlement/constants.py`. iOS reads them off the entitlement response so the SubscriptionView's "10 min/day, 30 min/week" copy stays in lockstep with whatever the backend enforces.
    free_minutes_per_day_cap: int
    free_minutes_per_week_cap: int
    premium_ends_at: datetime | None


@router.get("", response_model=EntitlementResponse)
async def fetch_entitlement(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> EntitlementResponse:
    if check_is_premium_now(user):
        return EntitlementResponse(
            is_premium=True,
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
        free_minutes_remaining_today=max(FREE_MINUTES_PER_DAY - used_today_minutes, 0),
        free_minutes_remaining_this_week=max(FREE_MINUTES_PER_WEEK - used_week_minutes, 0),
        free_minutes_per_day_cap=FREE_MINUTES_PER_DAY,
        free_minutes_per_week_cap=FREE_MINUTES_PER_WEEK,
        premium_ends_at=user["premium_ends_at"],
    )
