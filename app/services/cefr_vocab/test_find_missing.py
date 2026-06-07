from app.services.cefr_vocab._data import SORTED_BY_RANK
from app.services.cefr_vocab.find_missing import find_missing


def test_returns_up_to_limit() -> None:
    out = find_missing(used_lemmas=set(), limit=5)
    assert len(out) == 5


def test_skips_used_lemmas() -> None:
    # Use the first 3 entries by rank so they would otherwise appear in the result.
    used = {lemma for lemma, _entry in SORTED_BY_RANK[:3]}
    out = find_missing(used_lemmas=used, limit=10)
    out_lemmas = {lemma for lemma, _level in out}
    assert used.isdisjoint(out_lemmas)


def test_each_returned_tuple_carries_lemma_and_level() -> None:
    out = find_missing(used_lemmas=set(), limit=3)
    for lemma, level in out:
        assert isinstance(lemma, str) and lemma
        assert isinstance(level, str) and level
