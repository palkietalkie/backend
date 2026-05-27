from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentOut(BaseModel):
    personalization: bool
    product_improvement: bool
    set: bool


@router.get("", response_model=ConsentOut)
async def fetch_consent(user: UserRow = Depends(resolve_current_user)) -> ConsentOut:
    return ConsentOut(
        personalization=user["personalization_consent"] is not None,
        product_improvement=user["product_improvement_consent"] is not None,
        set=user["consent_screen_seen_at"] is not None,
    )
