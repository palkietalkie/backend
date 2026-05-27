from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today

router = APIRouter(prefix="/entitlement", tags=["entitlement"])


class EntitlementResponse(BaseModel):
    is_premium: bool
    free_minutes_remaining_today: int
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
            premium_ends_at=user["premium_ends_at"],
        )
    used_minutes = await sum_seconds_used_today(user, db) // 60
    remaining = max(FREE_MINUTES_PER_DAY - used_minutes, 0)
    return EntitlementResponse(
        is_premium=False,
        free_minutes_remaining_today=remaining,
        premium_ends_at=user["premium_ends_at"],
    )
