from app.services.cefr_vocab._data import BY_LEMMA
from app.services.cefr_vocab.constants import LEVELS


def count_used_by_level(used_lemmas: set[str]) -> dict[str, int]:
    counts: dict[str, int] = dict.fromkeys(LEVELS, 0)
    for lemma in used_lemmas:
        entry = BY_LEMMA.get(lemma)
        if entry is not None:
            counts[entry.level] += 1
    return counts
