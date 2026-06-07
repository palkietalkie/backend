"""How fast the tutor speaks in conversation. 5 levels. Default normal.

Beginners can't follow native tempo; advanced users get bored. Each level maps to a hint we inject into the system prompt ("speak slowly with long pauses" / "speak at normal pace" / "speak fast and conversationally").
"""

from typing import Literal, get_args

TutorSpeakingSpeed = Literal[
    "very_slow",
    "slow",
    "normal",
    "fast",
    "very_fast",
]

ALL_TUTOR_SPEAKING_SPEEDS: frozenset[TutorSpeakingSpeed] = frozenset(get_args(TutorSpeakingSpeed))
