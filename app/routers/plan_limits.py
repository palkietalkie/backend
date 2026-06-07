"""GET /plan_limits — public unauthenticated endpoint returning the current free-plan caps.

Single source of truth that the website pre-renders against so its pricing copy stays in sync with whatever the backend actually enforces. iOS already reads the same numbers off `/entitlement`, which is authenticated; this endpoint exists specifically so server-side rendering on the marketing site doesn't need a user session to print the right "X min/day, Y min/week" copy.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK

router = APIRouter(prefix="/plan_limits", tags=["plan_limits"])


class PlanLimitsResponse(BaseModel):
    free_minutes_per_day: int
    free_minutes_per_week: int


@router.get("", response_model=PlanLimitsResponse)
async def fetch_plan_limits() -> PlanLimitsResponse:
    return PlanLimitsResponse(
        free_minutes_per_day=FREE_MINUTES_PER_DAY,
        free_minutes_per_week=FREE_MINUTES_PER_WEEK,
    )
