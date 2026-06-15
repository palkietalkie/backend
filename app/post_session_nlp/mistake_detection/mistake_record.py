from dataclasses import dataclass


@dataclass(frozen=True)
class MistakeRecord:
    original: str
    corrected: str
    category: str
