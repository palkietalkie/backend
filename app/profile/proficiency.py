"""User-reported proficiency band, exposed in plain language. 5 levels, stored as the slug; iOS shows the display label.

`beginner` is a REAL from-zero beginner, not the old A1 that over-faced true starters. No "A0" level: it isn't a real CEFR band, and a true beginner can't self-classify finer than "beginner" anyway, so the tutor reads their level live. Per-level behavior and CEFR ranges live in build_proficiency_hint."""

from typing import Literal, get_args

Proficiency = Literal[
    "beginner",
    "lower_intermediate",
    "intermediate",
    "upper_intermediate",
    "advanced",
]

ALL_PROFICIENCIES: frozenset[Proficiency] = frozenset(get_args(Proficiency))
