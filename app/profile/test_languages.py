"""The languages catalog has a module-load assertion guaranteeing Literal ↔ LANGUAGES agreement. Test the public lookups + the accent invariant."""

import pytest

from app.profile.languages import (
    ALL_ACCENT_NAMES,
    LANGUAGE_NAMES,
    LANGUAGES,
    accent_belongs_to_language,
    get_language,
)


def test_get_language_returns_matching_entry() -> None:
    lang = get_language("English")
    assert lang.name == "English"
    assert len(lang.accents) > 0


def test_get_language_raises_for_unknown() -> None:
    with pytest.raises(KeyError):
        get_language("Not A Real Language Name")  # type: ignore[arg-type]


def test_accent_belongs_to_language_true() -> None:
    english = get_language("English")
    a_known_english_accent = english.accents[0]
    assert accent_belongs_to_language("English", a_known_english_accent)


def test_accent_belongs_to_language_false_for_wrong_pair() -> None:
    japanese = get_language("Japanese")
    a_japanese_accent = japanese.accents[0]
    assert not accent_belongs_to_language("English", a_japanese_accent)


def test_literal_types_agree_with_catalog() -> None:
    # Reinforces the module-load assertions inside languages.py — a broken refactor would surface here too.
    assert {lang.name for lang in LANGUAGES} == LANGUAGE_NAMES
    assert {a for lang in LANGUAGES for a in lang.accents} == ALL_ACCENT_NAMES
