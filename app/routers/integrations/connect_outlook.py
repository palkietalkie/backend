from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/outlook/connect")
async def connect_outlook(_user: UserRow = Depends(resolve_current_user)) -> dict[str, str]:
    # TODO: register app at https://entra.microsoft.com, add MS_OAUTH_* settings, copy connect_google_calendar logic with Microsoft endpoints.
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="outlook oauth not implemented yet"
    )
