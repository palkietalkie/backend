from typing import cast

from pydantic import BaseModel

from app.profile.languages import AccentName, LanguageName
from app.profile.proficiency import Proficiency
from app.profile.tutor_speaking_speed import TutorSpeakingSpeed
from app.services.neon.rows import UserRow


class ProfileOut(BaseModel):
    email: str | None
    display_name: str | None
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
    # DB columns are VARCHAR / TEXT[] — cast to the Literal types at this boundary. Values are guaranteed valid because every write path runs them through ProfileUpdate's validators.
    return ProfileOut(
        email=user["email"],
        display_name=user["display_name"],
        name_pronunciation=user["name_pronunciation"],
        name_pronunciation_suggestion=name_pronunciation_suggestion,
        native_languages=cast(list[LanguageName], user["native_languages"]),
        target_language=cast(LanguageName, user["target_language"]),
        target_accents=cast(list[AccentName], user["target_accents"]),
        proficiency=cast(Proficiency, user["proficiency"]),
        tutor_speaking_speed=cast(TutorSpeakingSpeed, user["tutor_speaking_speed"]),
        goals=user["goals"],
        location_city=user["location_city"],
        timezone=user["timezone"],
    )
