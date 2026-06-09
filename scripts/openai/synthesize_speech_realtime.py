import base64
import sys

import httpx

from app.services.openai.constants import (
    OPENAI_CHAT_AUDIO_MODEL,
    OPENAI_CHAT_COMPLETIONS_URL,
)


def synthesize_speech_realtime(client: httpx.Client, api_key: str, voice: str, text: str) -> bytes:
    """One-shot audio synthesis via `/v1/chat/completions` with audio modality.

    Covers `ballad` on top of the TTS-1 voice set the classic `/v1/audio/speech` endpoint exposes. `cedar`, `marin`, `verse` are still WebSocket-Realtime-only — `/v1/responses` rejected both `modalities` and `audio` keys, and `/v1/chat/completions` here rejects those three voices outright. To render samples for cedar/marin/verse, drive the Realtime WebSocket directly.

    Aborts the calling script on any non-2xx so we never write a truncated/corrupt sample to disk.
    """
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": OPENAI_CHAT_AUDIO_MODEL,
        "modalities": ["text", "audio"],
        "audio": {"voice": voice, "format": "wav"},
        "messages": [
            {
                "role": "user",
                "content": f"Say the following verbatim, with no preamble: {text}",
            }
        ],
    }
    r = client.post(OPENAI_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: Chat-audio TTS {voice} -> {r.status_code} {r.text}")
    body = r.json()
    audio_b64 = body["choices"][0]["message"].get("audio", {}).get("data")
    if not audio_b64:
        sys.exit(f"FAIL: Chat-audio TTS {voice} -> response had no audio: {body}")
    return base64.b64decode(audio_b64)
