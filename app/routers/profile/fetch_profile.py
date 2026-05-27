from fastapi import APIRouter, Depends

from app.auth.resolve_current_user import resolve_current_user
from app.routers.profile.build_profile_out import ProfileOut, build_profile_out
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
async def fetch_profile(user: UserRow = Depends(resolve_current_user)) -> ProfileOut:
    return build_profile_out(user)
