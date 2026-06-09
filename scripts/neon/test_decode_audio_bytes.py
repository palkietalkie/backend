"""Regression test for the gzip-vs-deflate session_audio bug.

iOS's `NSData.compressed(using: .zlib)` returns raw DEFLATE, but pre-fix builds labeled the upload `audio/wav+gzip` — the backend decoder accepted only gzip-magic bytes and fell through to garbage. These tests exercise the actual compression formats iOS could ever ship so the decoder never silently misreads bytes again.
"""

from __future__ import annotations

import gzip
import io
import zlib

import numpy as np
import soundfile as sf

from scripts.neon.decode_audio_bytes import decode_audio_bytes


def _make_wav_bytes() -> bytes:
    sr = 24000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    samples = (0.3 * np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
    buf = io.BytesIO()
    sf.write(buf, samples, sr, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def test_decode_raw_deflate_wav() -> None:
    wav = _make_wav_bytes()
    raw_deflate = zlib.compress(wav)[2:-4]
    audio, sr = decode_audio_bytes(raw_deflate)
    assert sr == 24000
    assert len(audio) == 24000


def test_decode_gzip_wrapped_wav() -> None:
    wav = _make_wav_bytes()
    gzipped = gzip.compress(wav)
    audio, sr = decode_audio_bytes(gzipped)
    assert sr == 24000
    assert len(audio) == 24000


def test_decode_zlib_wrapped_wav() -> None:
    wav = _make_wav_bytes()
    zlibbed = zlib.compress(wav)
    audio, sr = decode_audio_bytes(zlibbed)
    assert sr == 24000
    assert len(audio) == 24000


def test_decode_plain_wav_no_compression() -> None:
    wav = _make_wav_bytes()
    audio, sr = decode_audio_bytes(wav)
    assert sr == 24000
    assert len(audio) == 24000


def test_decode_raw_pcm16_fallback() -> None:
    sr = 24000
    samples = np.full(sr, 1000, dtype=np.int16).tobytes()
    audio, decoded_sr = decode_audio_bytes(samples)
    assert decoded_sr == 24000
    assert len(audio) == sr
    assert abs(audio[0] - 1000 / 32768.0) < 1e-4
