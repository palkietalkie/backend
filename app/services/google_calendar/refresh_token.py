"""Google OAuth token refresh.

Single responsibility: given a stored ``CalendarTokenRow`` whose access token has expired (or is
about to), call Google's token endpoint to refresh and persist the new access token + expiry.
"""

from datetime import UTC, datetime, timedelta

import httpx

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import CalendarTokenRow

TOKEN_URL = "https://oauth2.googleapis.com/token"  # noqa: S105 — endpoint URL, not a secret


async def refresh_token(token: CalendarTokenRow, db: DBConn) -> None:
    """Refresh the Google access token in place. No-op if there is no refresh token."""
    settings = get_settings()
    if not token["refresh_token"]:
        return
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "refresh_token": token["refresh_token"],
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    new_expires = (
        datetime.now(UTC) + timedelta(seconds=int(data["expires_in"]))
        if "expires_in" in data
        else None
    )
    await db.execute(
        """UPDATE calendar_tokens
           SET access_token = $2, expires_at = $3, updated_at = NOW()
           WHERE id = $1""",
        token["id"],
        data["access_token"],
        new_expires,
    )
    token["access_token"] = data["access_token"]
    token["expires_at"] = new_expires
