from dataclasses import dataclass


@dataclass(frozen=True)
class CefrEntry:
    level: str
    rank: int
