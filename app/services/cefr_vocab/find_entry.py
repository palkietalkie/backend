from app.services.cefr_vocab._data import BY_LEMMA
from app.services.cefr_vocab.cefr_entry import CefrEntry


def find_entry(lemma: str) -> CefrEntry | None:
    return BY_LEMMA.get(lemma)
