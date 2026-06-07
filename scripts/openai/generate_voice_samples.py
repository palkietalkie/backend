# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "numpy>=2.0", "soundfile>=0.12", "pyloudnorm>=0.1.1"]
# ///
"""Generate one short audio sample per OpenAI voice and drop the wavs into the iOS bundle.

Orchestrator only. Two synthesis paths sit behind the per-voice loop: - voices the classic TTS endpoint exposes → `synthesize_speech` (`/v1/audio/speech`) - realtime-only voices → `synthesize_speech_realtime` (`/v1/responses` with audio modality)

The voice list mirrors `OpenAIVoiceId` in `app/services/openai/constants.py` so we cover every voice the Realtime API offers, not just the cheaper TTS subset.

Cost: a few cents per full run; the script skips wavs that already exist so re-runs are free.

Run: `OPENAI_API_KEY=… cd backend && uv run scripts/openai/generate_voice_samples.py`"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.openai.constants import OpenAIVoiceId  # noqa: E402
from scripts.openai.normalize_loudness import normalize_loudness  # noqa: E402
from scripts.openai.sample_line import sample_line  # noqa: E402
from scripts.openai.synthesize_speech import synthesize_speech  # noqa: E402
from scripts.openai.synthesize_speech_realtime import synthesize_speech_realtime  # noqa: E402

# Voices the classic `/v1/audio/speech` endpoint accepts (rejects anything else with HTTP 400). Everything else routes through the Realtime responses endpoint.
TTS_VOICES: frozenset[str] = frozenset({"alloy", "ash", "coral", "echo", "sage", "shimmer"})

OUT_DIR = (
    Path(__file__).resolve().parents[3] / "ios" / "PalkieTalkie" / "Resources" / "VoiceSamples"
)


def main() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        sys.exit("FAIL: OPENAI_API_KEY env var is required.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client(timeout=120.0) as client:
        for voice in OpenAIVoiceId:
            target = OUT_DIR / f"{voice.value}.wav"
            if target.exists() and target.stat().st_size > 0:
                print(f"[tts] skip {voice.value} (already exists)")
                continue
            text = sample_line(voice.value)
            if voice.value in TTS_VOICES:
                audio_bytes = synthesize_speech(client, api_key, voice.value, text)
                path = "/v1/audio/speech"
            else:
                audio_bytes = synthesize_speech_realtime(client, api_key, voice.value, text)
                path = "/v1/chat/completions"
            audio_bytes = normalize_loudness(audio_bytes, target_lufs=-19.0, peak_ceiling_dbfs=-1.0)
            target.write_bytes(audio_bytes)
            print(
                f"[tts] wrote {target.relative_to(OUT_DIR.parents[3])} "
                f"({len(audio_bytes)} bytes via {path})"
            )


if __name__ == "__main__":
    main()
