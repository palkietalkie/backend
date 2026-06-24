"""How fast the tutor speaks in conversation. 5 levels. Default normal.

Beginners can't follow native tempo; advanced users get bored. Each level maps to BOTH a concrete playback-rate (a real slowdown of the audio) and a system-prompt hint ("speak slowly with long pauses" / "speak at normal pace" / "speak fast and conversationally"). OpenAI recommends combining the two: the rate guarantees the slowdown, the hint shapes the natural cadence.
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

# Concrete playback-rate per level, fed to OpenAI Realtime's session.audio.output.speed (a real post-processing slowdown of the generated audio, NOT just the prompt hint). The prompt hint alone is unreliable: realtime models drift back to native pace within a few turns, so a beginner who set very_slow/slow still got firehosed. These give a guaranteed slowdown. OpenAI's accepted range is 0.25-1.5 (1.0 = natural); kept moderate so slowed speech stays natural, not underwater.
TUTOR_SPEED_PLAYBACK_RATE: dict[TutorSpeakingSpeed, float] = {
    "very_slow": 0.7,
    "slow": 0.85,
    "normal": 1.0,
    "fast": 1.15,
    "very_fast": 1.3,
}

# Maps any string (a raw DB value) back to a known level, defaulting to "normal". Lets callers narrow `users.tutor_speaking_speed` (typed as plain str) to the Literal without a cast, and keeps a stale/null value from crashing the speed lookup.
_BY_NAME: dict[str, TutorSpeakingSpeed] = {s: s for s in ALL_TUTOR_SPEAKING_SPEEDS}


def coerce_speaking_speed(raw: str | None) -> TutorSpeakingSpeed:
    return _BY_NAME.get(raw or "", "normal")
