from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/integrations", tags=["integrations"])


class ProviderStatus(BaseModel):
    provider: str
    connected: bool
    expires_at: datetime | None


@router.get("", response_model=list[ProviderStatus])
async def list_integrations(
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> list[ProviderStatus]:
    rows = await db.fetch(
        """SELECT id, user_id, provider, access_token, refresh_token, expires_at, created_at, updated_at
           FROM calendar_tokens
           WHERE user_id = $1""",
        user["id"],
    )
    by_provider = {row["provider"]: row for row in rows}
    return [
        ProviderStatus(
            provider=p,
            connected=p in by_provider,
            expires_at=by_provider[p]["expires_at"] if p in by_provider else None,
        )
        for p in ("google", "apple", "outlook")
    ]
