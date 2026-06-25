from app.personas.presets.preset_text_translations import PRESET_TEXT

_LOCALES = {"ja", "zh-Hans", "zh-Hant", "ko", "es", "pt-BR", "fr", "de", "vi", "id", "hi"}


def test_every_entry_carries_all_eleven_locales() -> None:
    for english, translations in PRESET_TEXT.items():
        assert set(translations) == _LOCALES, f"{english!r} missing {_LOCALES - set(translations)}"


def test_all_translations_are_nonempty() -> None:
    for english, translations in PRESET_TEXT.items():
        for locale, value in translations.items():
            assert value.strip(), f"{english!r} / {locale} is empty"


def test_journaling_companion_name_and_description_translated() -> None:
    # The journaling-companion preset's user-facing name + description must be fully localized across all 11 targets.
    name = "Journaling companion"
    description = (
        "Talks through your day or your thoughts and helps you organize them out loud. "
        "Gentle and low-pressure."
    )
    for key in (name, description):
        assert key in PRESET_TEXT, f"{key!r} missing from PRESET_TEXT"
        assert set(PRESET_TEXT[key]) == _LOCALES
