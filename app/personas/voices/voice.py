from dataclasses import dataclass


@dataclass(frozen=True)
class Voice:
    id: str
    label: str
    gender: str
    description: str
