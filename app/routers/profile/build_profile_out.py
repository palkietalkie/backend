from pydantic import BaseModel

from app.profile.languages import AccentName, LanguageName
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.services.neon.rows import UserRow


class ProfileOut(BaseModel):
    email: str | None
    preferred_name: str | None
    name_pronunciation: str | None
    # Placeholder pronunciation hint computed on GET when `name_pronunciation` is empty. Never persisted — iOS shows it as a TextField placeholder so the user sees a suggestion they can either accept (type to confirm) or ignore (leave blank).
    name_pronunciation_suggestion: str | None = None
    native_languages: list[LanguageName]
    target_language: LanguageName
    target_accents: list[AccentName]
    proficiency: Proficiency
    tutor_speaking_speed: TutorSpeakingSpeed
    goals: str | None
    location_city: str | None
    timezone: str | None


def build_profile_out(
    user: UserRow,
    name_pronunciation_suggestion: str | None = None,
) -> ProfileOut:
    # DB columns are VARCHAR / TEXT[]; model_validate checks the plain str / list[str] against the Literal field types at runtime. Every write path already ran them through ProfileUpdate's validators, so they pass — and a drift (DB value outside the Literal) now fails loud instead of slipping through a cast.
    return ProfileOut.model_validate(
        {**user, "name_pronunciation_suggestion": name_pronunciation_suggestion}
    )
