"""Regression tests for the voice-RMS / inactivity thresholds.

Pins them against representative silent / ambient / speaking PCM so a future tweak doesn't
accidentally let "mic on, no voice" hold the GPU again.
"""

from __future__ import annotations

import numpy as np

from inference.inactivity_thresholds import (
    PALKIE_INACTIVITY_TIMEOUT_S,
    PALKIE_VOICE_RMS_THRESHOLD,
)


def _rms(pcm: np.ndarray) -> float:
    """Mirror the formula opus_loop uses to gate inactivity."""
    return float(np.sqrt(np.mean(pcm * pcm)))


def test_silent_chunk_falls_under_voice_threshold() -> None:
    silent = np.zeros(1920, dtype=np.float32)
    assert _rms(silent) < PALKIE_VOICE_RMS_THRESHOLD


def test_quiet_room_ambient_falls_under_voice_threshold() -> None:
    rng = np.random.default_rng(0)
    ambient = rng.normal(0, 0.003, 1920).astype(np.float32)
    assert _rms(ambient) < PALKIE_VOICE_RMS_THRESHOLD


def test_speaking_voice_clears_voice_threshold() -> None:
    rng = np.random.default_rng(0)
    voice = rng.normal(0, 0.1, 1920).astype(np.float32)
    assert _rms(voice) > PALKIE_VOICE_RMS_THRESHOLD


def test_inactivity_timeout_pinned_to_one_minute() -> None:
    """If this fails, someone bumped the timeout — check that's actually what they intended."""
    assert PALKIE_INACTIVITY_TIMEOUT_S == 60.0
