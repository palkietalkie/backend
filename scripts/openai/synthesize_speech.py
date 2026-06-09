import sys

import httpx

from app.services.openai.constants import OPENAI_TTS_MODEL, OPENAI_TTS_URL


def synthesize_speech(
    client: httpx.Client, api_key: str, voice: str, text: str, response_format: str = "wav"
) -> bytes:
    """Call OpenAI's classic `/v1/audio/speech` and return the rendered audio bytes.

    Limited to the TTS-1 voice set (`alloy`, `ash`, `coral`, `echo`, `sage`, `shimmer`). For voices only exposed via the Realtime API (`ballad`, `cedar`, `marin`, `verse`) use `synthesize_speech_realtime` instead. Aborts the calling script on any non-2xx so we never write a truncated/corrupt sample to disk.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_TTS_MODEL,
        "input": text,
        "voice": voice,
        "response_format": response_format,
    }
    r = client.post(OPENAI_TTS_URL, headers=headers, json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: TTS {voice} -> {r.status_code} {r.text}")
    return r.content
