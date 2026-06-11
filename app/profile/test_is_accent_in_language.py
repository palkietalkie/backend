from app.profile.get_language import get_language
from app.profile.is_accent_in_language import is_accent_in_language


def test_is_accent_in_language_true() -> None:
    a_known_english_accent = get_language("English").accents[0]
    assert is_accent_in_language("English", a_known_english_accent)


def test_is_accent_in_language_false_for_wrong_pair() -> None:
    a_japanese_accent = get_language("Japanese").accents[0]
    assert not is_accent_in_language("English", a_japanese_accent)
