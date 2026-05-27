from app.services.cefr_vocab._data import SORTED_BY_RANK


def find_missing(used_lemmas: set[str], limit: int) -> list[tuple[str, str]]:
    """Words across all levels NOT in `used_lemmas`, sorted by rank (most common first)."""
    out: list[tuple[str, str]] = []
    for lemma, entry in SORTED_BY_RANK:
        if lemma in used_lemmas:
            continue
        out.append((lemma, entry.level))
        if len(out) >= limit:
            break
    return out
