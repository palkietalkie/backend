from app.profile.languages import LANGUAGES, Language, LanguageName

# Indexed once at import. The module-load invariant in languages.py guarantees every LanguageName is present, so the lookup is total for any type-valid name — no fallthrough branch to cover.
_BY_NAME: dict[LanguageName, Language] = {lang.name: lang for lang in LANGUAGES}


def get_language(name: LanguageName) -> Language:
    return _BY_NAME[name]
