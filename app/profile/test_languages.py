"""The languages catalog carries module-load assertions guaranteeing Literal ↔ LANGUAGES agreement. This re-checks that invariant from the test suite so a broken refactor surfaces here too."""

from app.profile.languages import ALL_ACCENT_NAMES, LANGUAGE_NAMES, LANGUAGES


def test_literal_types_agree_with_catalog() -> None:
    assert {lang.name for lang in LANGUAGES} == LANGUAGE_NAMES
    assert {a for lang in LANGUAGES for a in lang.accents} == ALL_ACCENT_NAMES
