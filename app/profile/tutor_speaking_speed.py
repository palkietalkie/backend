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

# Concrete playback-rate per level, fed to OpenAI Realtime's session.audio.output.speed (a real post-processing slowdown of the generated audio). This is the ONLY working speed control: a prompt-based pace lever (telling the model a target words-per-minute) was tested against the real API and has NO measurable effect, the realtime model ignores pace instructions and reverts to ~210 wpm regardless (measured 216 vs 206 wpm for a "90 wpm" vs "210 wpm" prompt with playback pinned at 1.0; see app/services/openai/test_manual_openai_speed.py). So don't re-add a prompt pace hint expecting it to work; audio.output.speed carries the whole effect.
# Kept GENTLE (extremes within ±0.20 of natural): audio.output.speed is a time-stretch, and past roughly that the speech starts to sound artificial / processed. Testers including a beginner (Ayumi, the very reason the slow end exists) flagged the stronger 0.7/1.3 ends as unnatural, so the extremes are pulled toward 1.0, trading some slowdown/speedup for audio that still sounds like a person. OpenAI's accepted range is 0.25-1.5 (1.0 = natural).
TUTOR_SPEED_PLAYBACK_RATE: dict[TutorSpeakingSpeed, float] = {
    "very_slow": 0.8,
    "slow": 0.9,
    "normal": 1.0,
    "fast": 1.1,
    "very_fast": 1.2,
}

# Maps any string (a raw DB value) back to a known level, defaulting to "normal". Lets callers narrow `users.tutor_speaking_speed` (typed as plain str) to the Literal without a cast, and keeps a stale/null value from crashing the speed lookup.
_BY_NAME: dict[str, TutorSpeakingSpeed] = {s: s for s in ALL_TUTOR_SPEAKING_SPEEDS}


def coerce_speaking_speed(raw: str | None) -> TutorSpeakingSpeed:
    return _BY_NAME.get(raw or "", "normal")
