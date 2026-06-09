import uuid
from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/google-calendar/callback")
async def handle_google_calendar_callback(
    code: str = Query(),
    state: str = Query(),
    db: DBConn = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_oauth_client_id,
                "client_secret": settings.google_oauth_client_secret,
                "redirect_uri": settings.google_oauth_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        data = resp.json()

    user_row = await db.fetchrow(
        """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                  display_name, name_pronunciation,
                  native_languages, target_language, target_accents, proficiency, tutor_speaking_speed, goals,
                  location_city, timezone,
                  personalization_consent, product_improvement_consent, consent_screen_seen_at
           FROM users
           WHERE clerk_user_id = $1""",
        state,
    )
    if user_row is None:
        raise HTTPException(status_code=400, detail="unknown user state")

    expires_in = int(data.get("expires_in", 0))
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in) if expires_in else None

    await db.execute(
        """INSERT INTO calendar_tokens (id, user_id, provider, access_token, refresh_token, expires_at)
           VALUES ($1, $2, $3, $4, $5, $6)
           ON CONFLICT ON CONSTRAINT uq_calendar_user_provider DO UPDATE SET
               access_token  = EXCLUDED.access_token,
               refresh_token = COALESCE(EXCLUDED.refresh_token, calendar_tokens.refresh_token),
               expires_at    = EXCLUDED.expires_at,
               updated_at    = NOW()""",
        uuid.uuid4(),
        user_row["id"],
        "google",
        data["access_token"],
        data.get("refresh_token"),
        expires_at,
    )

    return RedirectResponse(url="palkietalkie://integrations/google-calendar/connected")
