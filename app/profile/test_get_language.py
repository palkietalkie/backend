from app.profile.get_language import get_language


def test_get_language_returns_matching_entry() -> None:
    lang = get_language("English")
    assert lang.name == "English"
    assert len(lang.accents) > 0
