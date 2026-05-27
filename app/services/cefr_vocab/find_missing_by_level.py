from app.services.cefr_vocab._data import BY_LEVEL


def find_missing_by_level(used_lemmas: set[str], level: str, limit: int) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for lemma, _rank in BY_LEVEL.get(level, []):
        if lemma in used_lemmas:
            continue
        out.append((lemma, level))
        if len(out) >= limit:
            break
    return out
