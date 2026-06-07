"""Loudness-normalize a WAV byte string to a target LUFS, with peak limiting to prevent clipping."""

from __future__ import annotations

import io

import numpy as np
import pyloudnorm as pyln
import soundfile as sf


def normalize_loudness(
    wav_bytes: bytes, target_lufs: float = -16.0, peak_ceiling_dbfs: float = -1.0
) -> bytes:
    audio, sr = sf.read(io.BytesIO(wav_bytes), dtype="float32")
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    meter = pyln.Meter(sr)
    loudness = meter.integrated_loudness(audio.astype(np.float64))
    normalized = pyln.normalize.loudness(audio, loudness, target_lufs)
    peak = float(np.max(np.abs(normalized)))
    ceiling = 10 ** (peak_ceiling_dbfs / 20)
    if peak > ceiling:
        normalized = normalized * (ceiling / peak)
    pcm16 = np.clip(normalized * 32767.0, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, pcm16, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()
