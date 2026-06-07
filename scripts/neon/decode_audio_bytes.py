"""Decode session_audio bytes into ``(samples, sr)``.

Probes in this order: gzip header, zlib header, raw DEFLATE (the format iOS actually ships — Apple's `NSData.compressed(using: .zlib)` despite its name produces raw DEFLATE, not zlib-wrapped). Then container WAV via soundfile, finally raw PCM16 mono @ 24kHz as a last-resort interpretation. The `format` column on session_audio is informational only — a pre-2026-06 iOS build mislabeled raw-deflate bytes as `audio/wav+gzip`, so we can't trust it.
"""

from __future__ import annotations

import gzip
import io
import zlib

import numpy as np
import soundfile as sf


def _try_decompress(raw: bytes) -> bytes:
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    if raw[0] == 0x78 and (raw[0] * 256 + raw[1]) % 31 == 0:
        return zlib.decompress(raw)
    try:
        return zlib.decompress(raw, -zlib.MAX_WBITS)
    except zlib.error:
        return raw


def decode_audio_bytes(raw: bytes) -> tuple[np.ndarray, int]:
    raw = _try_decompress(raw)
    try:
        audio, sr = sf.read(io.BytesIO(raw), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        return audio.astype(np.float64), int(sr)
    except (sf.LibsndfileError, RuntimeError, ValueError):  # fmt: skip
        n_pcm = len(raw) // 2 * 2
        pcm = np.frombuffer(raw[:n_pcm], dtype="<i2").astype(np.float64) / 32768.0
        return pcm, 24000
