from app.personas.presets.preset_text_translations import PRESET_TEXT

_LOCALES = {"ja", "zh-Hans", "zh-Hant", "ko", "es", "pt-BR", "fr", "de", "vi", "id", "hi"}


def test_every_entry_carries_all_eleven_locales() -> None:
    for english, translations in PRESET_TEXT.items():
        assert set(translations) == _LOCALES, f"{english!r} missing {_LOCALES - set(translations)}"


def test_all_translations_are_nonempty() -> None:
    for english, translations in PRESET_TEXT.items():
        for locale, value in translations.items():
            assert value.strip(), f"{english!r} / {locale} is empty"
