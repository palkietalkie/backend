from app.services.cefr_vocab._data import BY_LEVEL
from app.services.cefr_vocab.find_missing_by_level import find_missing_by_level


def test_returns_up_to_limit_for_a_real_level() -> None:
    level = next(iter(BY_LEVEL.keys()))
    out = find_missing_by_level(used_lemmas=set(), level=level, limit=4)
    assert len(out) == 4
    # Every returned tuple is tagged with the requested level.
    assert all(returned_level == level for _, returned_level in out)


def test_unknown_level_returns_empty() -> None:
    assert find_missing_by_level(used_lemmas=set(), level="bogus", limit=10) == []


def test_excludes_used_lemmas() -> None:
    level, entries = next(iter(BY_LEVEL.items()))
    used = {entries[0][0]}  # the top-ranked lemma at this level
    out = find_missing_by_level(used_lemmas=used, level=level, limit=5)
    assert all(lemma not in used for lemma, _ in out)
