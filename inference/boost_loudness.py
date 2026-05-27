"""Loudness post-processing for PersonaPlex/Mimi audio output.

PersonaPlex's Mimi decoder produces quiet PCM (peaks ~0.05-0.4) which sounds underleveled on iOS
speakers. Lifts each chunk's peak toward a conversational target with bounded gain (so silent
frames don't get amplified) and a hard per-sample ceiling (so we never clip past ±0.95).

Bundled into the Modal container image at /root/boost_loudness.py via voice_image.py so
moshi/server.py's opus_loop can import and call it.
"""

from __future__ import annotations

import numpy as np

PALKIE_TARGET_PEAK = 0.85
PALKIE_MAX_GAIN = 8.0
PALKIE_CEILING = 0.95


def boost_loudness(pcm: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(pcm))) if pcm.size else 0.0
    if peak < 1e-4:
        return pcm
    desired_gain = PALKIE_TARGET_PEAK / peak
    gain = min(desired_gain, PALKIE_MAX_GAIN)
    out = pcm * gain
    return np.clip(out, -PALKIE_CEILING, PALKIE_CEILING)
