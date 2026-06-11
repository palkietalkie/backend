from app.profile.get_language import get_language
from app.profile.languages import AccentName, LanguageName


def is_accent_in_language(language_name: LanguageName, accent_name: AccentName) -> bool:
    return accent_name in get_language(language_name).accents
