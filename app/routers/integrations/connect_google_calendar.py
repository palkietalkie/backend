from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/integrations", tags=["integrations"])

GOOGLE_SCOPES = ["https://www.googleapis.com/auth/calendar.readonly", "openid", "email"]


class ConnectURL(BaseModel):
    auth_url: str


@router.post("/google-calendar/connect", response_model=ConnectURL)
async def connect_google_calendar(user: UserRow = Depends(resolve_current_user)) -> ConnectURL:
    # State carries the Clerk user id so the callback knows whose token to save.
    settings = get_settings()
    if not settings.google_oauth_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="google oauth not configured",
        )
    params = {
        "client_id": settings.google_oauth_client_id,
        "redirect_uri": settings.google_oauth_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": user["clerk_user_id"],
    }
    return ConnectURL(auth_url=f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}")
