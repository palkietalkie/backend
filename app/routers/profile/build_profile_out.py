from typing import get_args

from pydantic import BaseModel

from app.profile.languages import AccentName, LanguageName
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.services.neon.rows import UserRow

_VALID_LANGUAGES = frozenset(get_args(LanguageName))
_VALID_ACCENTS = frozenset(get_args(AccentName))
_VALID_PROFICIENCY = frozenset(get_args(Proficiency))
_VALID_SPEED = frozenset(get_args(TutorSpeakingSpeed))


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
    # GET /profile must NEVER 500 on a stale enum value. The TestFlight build in App Review aborts its ENTIRE profile screen (blank, untappable pickers) the instant this read fails, and that build is frozen during the Apple account conversion, so no client fix can ship. If a stored value drifted outside the current Literal (e.g. an accent we later renamed), coerce it to a safe default here instead of raising. Writes still validate strictly via ProfileUpdate, so this only softens reads of already-persisted data.
    coerced = {
        **user,
        "target_language": user["target_language"]
        if user["target_language"] in _VALID_LANGUAGES
        else "English",
        "proficiency": user["proficiency"]
        if user["proficiency"] in _VALID_PROFICIENCY
        else "intermediate",
        "tutor_speaking_speed": user["tutor_speaking_speed"]
        if user["tutor_speaking_speed"] in _VALID_SPEED
        else "normal",
        "native_languages": [lang for lang in user["native_languages"] if lang in _VALID_LANGUAGES],
        "target_accents": [accent for accent in user["target_accents"] if accent in _VALID_ACCENTS],
        "name_pronunciation_suggestion": name_pronunciation_suggestion,
    }
    return ProfileOut.model_validate(coerced)
