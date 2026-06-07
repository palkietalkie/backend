"""User-reported proficiency band, CEFR-aligned but exposed in plain language.

Maps to CEFR levels:
- beginner ↔ A1
- lower_intermediate ↔ A2
- intermediate ↔ B1
- upper_intermediate ↔ B2
- advanced ↔ C1+

Stored as the slug (`beginner`, `lower_intermediate`, …) in the DB. iOS shows the display label."""

from typing import Literal, get_args

Proficiency = Literal[
    "beginner",
    "lower_intermediate",
    "intermediate",
    "upper_intermediate",
    "advanced",
]

ALL_PROFICIENCIES: frozenset[Proficiency] = frozenset(get_args(Proficiency))
