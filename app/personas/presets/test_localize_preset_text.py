from app.personas.presets.localize_preset_text import localize_preset_text


def test_returns_translation_for_known_text_and_locale() -> None:
    assert localize_preset_text("A man", "ja") == "男性"


def test_falls_back_to_english_for_unknown_text() -> None:
    assert localize_preset_text("a string with no translation entry", "ja") == (
        "a string with no translation entry"
    )


def test_falls_back_to_english_for_untranslated_locale() -> None:
    # Known English string, but a locale we don't carry: return the canonical English unchanged.
    assert localize_preset_text("A man", "xx-Unknown") == "A man"
