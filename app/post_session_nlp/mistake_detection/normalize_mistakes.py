from pydantic import BaseModel, ValidationError

from app.post_session_nlp.mistake_detection.constants import VALID_CATEGORIES
from app.post_session_nlp.mistake_detection.mistake_record import MistakeRecord


class _MistakeIn(BaseModel):
    original: str
    corrected: str
    category: str


def normalize_mistakes(raw: list[object]) -> list[MistakeRecord]:
    out: list[MistakeRecord] = []
    for item in raw:
        try:
            m = _MistakeIn.model_validate(item)
        except ValidationError:
            continue
        if m.category not in VALID_CATEGORIES:
            continue
        if m.original.strip() == m.corrected.strip():
            continue
        out.append(MistakeRecord(original=m.original, corrected=m.corrected, category=m.category))
    return out
