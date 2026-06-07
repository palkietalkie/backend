from app.services.cefr_vocab._data import BY_LEMMA
from app.services.cefr_vocab.constants import LEVELS
from app.services.cefr_vocab.count_used_by_level import count_used_by_level


def test_returns_zero_for_each_level_on_empty_input() -> None:
    counts = count_used_by_level(set())
    assert set(counts.keys()) == set(LEVELS)
    assert all(v == 0 for v in counts.values())


def test_counts_known_lemma_at_its_level() -> None:
    # Pick a real lemma from the CEFR data so we exercise the lookup path against the real corpus.
    lemma, entry = next(iter(BY_LEMMA.items()))
    counts = count_used_by_level({lemma})
    assert counts[entry.level] == 1
    # Every other level stays at zero.
    for level in LEVELS:
        if level != entry.level:
            assert counts[level] == 0


def test_unknown_lemma_is_silently_skipped() -> None:
    counts = count_used_by_level({"zzzzz-not-a-real-word"})
    assert all(v == 0 for v in counts.values())
