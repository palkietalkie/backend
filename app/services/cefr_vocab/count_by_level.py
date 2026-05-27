from app.services.cefr_vocab._data import BY_LEVEL


def count_by_level() -> dict[str, int]:
    return {level: len(lemmas) for level, lemmas in BY_LEVEL.items()}
