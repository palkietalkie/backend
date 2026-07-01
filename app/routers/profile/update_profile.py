from typing import Self

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator

from app.auth.resolve_current_user import resolve_current_user
from app.profile.correction_frequency import CorrectionFrequency
from app.profile.is_accent_in_language import is_accent_in_language
from app.profile.is_language_name import is_language_name
from app.profile.languages import AccentName, LanguageName
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.routers.profile.build_profile_out import ProfileOut, build_profile_out
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.make_rows import make_user_row
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/profile", tags=["profile"])


class ProfileUpdate(BaseModel):
    preferred_name: str | None = Field(default=None, max_length=120)
    name_pronunciation: str | None = Field(default=None, max_length=120)
    native_languages: list[LanguageName] | None = Field(default=None, min_length=1)
    target_language: LanguageName | None = None
    target_accents: list[AccentName] | None = None
    proficiency: Proficiency | None = None
    tutor_speaking_speed: TutorSpeakingSpeed | None = None
    correction_frequency: CorrectionFrequency | None = None
    goals: str | None = None
    location_city: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, max_length=64)

    @model_validator(mode="after")
    def _accents_belong_to_language(self) -> Self:
        # If a PATCH sets both fields, EVERY chosen accent must belong to the language. If only target_accents is sent, the route handler validates against the user's existing target_language.
        if self.target_language is None or self.target_accents is None:
            return self
        for accent in self.target_accents:
            if not is_accent_in_language(self.target_language, accent):
                raise ValueError(
                    f"accent {accent!r} is not valid for language {self.target_language!r}"
                )
        return self


@router.patch("", response_model=ProfileOut)
async def update_profile(
    body: ProfileUpdate,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> ProfileOut:
    if body.target_accents is not None and body.target_language is None:
        effective_language = user["target_language"]
        if not is_language_name(effective_language):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"stored target language {effective_language!r} is not a recognized language",
            )
        for accent in body.target_accents:
            if not is_accent_in_language(effective_language, accent):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"accent {accent!r} is not valid for current language {effective_language!r}",
                )

    row = await db.fetchrow(
        """UPDATE users
           SET preferred_name   = COALESCE($2, preferred_name),
               name_pronunciation   = COALESCE($3, name_pronunciation),
               native_languages     = COALESCE($4, native_languages),
               target_language      = COALESCE($5, target_language),
               target_accents       = COALESCE($6, target_accents),
               proficiency          = COALESCE($7, proficiency),
               tutor_speaking_speed = COALESCE($8, tutor_speaking_speed),
               goals                = COALESCE($9, goals),
               location_city        = COALESCE($10, location_city),
               timezone             = COALESCE($11, timezone),
               correction_frequency = COALESCE($12, correction_frequency),
               updated_at           = NOW()
           WHERE id = $1
           RETURNING id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                     preferred_name, name_pronunciation,
                     native_languages, target_language, target_accents,
                     proficiency, tutor_speaking_speed, correction_frequency,
                     goals, location_city, timezone,
                     personalization_consent, product_improvement_consent, consent_screen_seen_at""",
        user["id"],
        body.preferred_name,
        body.name_pronunciation,
        body.native_languages,
        body.target_language,
        body.target_accents,
        body.proficiency,
        body.tutor_speaking_speed,
        body.goals,
        body.location_city,
        body.timezone,
        body.correction_frequency,
    )
    assert row is not None
    updated = make_user_row(row)
    # No auto-fill here. If the user PATCHes an empty pronunciation, that's an explicit clear and we respect it. The suggestion shown to the user in the UI comes from GET /profile (placeholder, not persisted).
    return build_profile_out(updated)
