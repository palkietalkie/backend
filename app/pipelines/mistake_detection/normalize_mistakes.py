from typing import Any

from app.pipelines.mistake_detection.constants import VALID_CATEGORIES
from app.pipelines.mistake_detection.mistake_record import MistakeRecord


def normalize_mistakes(raw: list[Any]) -> list[MistakeRecord]:
    out: list[MistakeRecord] = []
    for m in raw:
        if not isinstance(m, dict):
            continue
        original = m.get("original")
        corrected = m.get("corrected")
        category = m.get("category")
        if not (
            isinstance(original, str) and isinstance(corrected, str) and isinstance(category, str)
        ):
            continue
        if category not in VALID_CATEGORIES:
            continue
        if original.strip() == corrected.strip():
            continue
        out.append(MistakeRecord(original=original, corrected=corrected, category=category))
    return out
