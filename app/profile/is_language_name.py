from typing import TypeGuard

from app.profile.languages import LANGUAGE_NAMES, LanguageName


def is_language_name(value: str) -> TypeGuard[LanguageName]:
    return value in LANGUAGE_NAMES
