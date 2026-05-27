from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.routers.profile.build_profile_out import ProfileOut, build_profile_out
from app.services.neon.db_conn import DBConn
from app.services.neon.get_db import get_db
from app.services.neon.make_rows import make_user_row
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    name_pronunciation: str | None = Field(default=None, max_length=120)
    native_language: str | None = Field(default=None, max_length=32)
    target_accent: str | None = Field(default=None, max_length=32)
    goals: str | None = None
    location_city: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)


@router.patch("", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_db),
) -> ProfileOut:
    row = await db.fetchrow(
        """UPDATE users
           SET display_name       = COALESCE($2, display_name),
               name_pronunciation = COALESCE($3, name_pronunciation),
               native_language    = COALESCE($4, native_language),
               target_accent      = COALESCE($5, target_accent),
               goals              = COALESCE($6, goals),
               location_city      = COALESCE($7, location_city),
               timezone           = COALESCE($8, timezone),
               updated_at         = NOW()
           WHERE id = $1
           RETURNING id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                     display_name, name_pronunciation,
                     native_language, target_accent, goals,
                     location_city, timezone,
                     personalization_consent, product_improvement_consent, consent_screen_seen_at""",
        user["id"],
        body.display_name,
        body.name_pronunciation,
        body.native_language,
        body.target_accent,
        body.goals,
        body.location_city,
        body.timezone,
    )
    assert row is not None
    return build_profile_out(make_user_row(row))
