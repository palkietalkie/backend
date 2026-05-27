"""OpenAI Realtime API session minter (GA, not Beta).

Alternative inference path to PersonaPlex. Backend calls OpenAI's GA endpoint
``/v1/realtime/client_secrets`` to mint a short-lived ephemeral token (default 10
min TTL, configurable up to 2h), which iOS uses to open a WebSocket directly to
``wss://api.openai.com/v1/realtime?model=gpt-realtime-mini``. The audio + text protocol
on that WS is JSON event frames (``input_audio_buffer.append`` going out,
``response.audio.delta`` coming back), NOT the binary Ogg-Opus protocol the
PersonaPlex path speaks. iOS picks the wire format based on the ``provider`` field
on ``StartResponse``.

This used to call the Beta endpoint ``/v1/realtime/sessions`` with the
``OpenAI-Beta: realtime=v1`` header; OpenAI killed the Beta shape entirely
(``beta_api_shape_disabled``) so the GA contract is the only path now. Source of
truth for the GA shape: openai/openai-python ``src/openai/resources/realtime/``
and ``src/openai/types/realtime/*``.
"""

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings
from app.services.openai.constants import (
    OPENAI_CLIENT_SECRETS_URL,
    OPENAI_REALTIME_MODEL,
    OPENAI_REALTIME_WS_URL,
    OpenAIVoiceId,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OpenAISession:
    ws_url: str
    ephemeral_token: str
    voice_id: OpenAIVoiceId


async def mint_openai_session(
    text_prompt: str,
    voice_id: OpenAIVoiceId,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> OpenAISession:
    settings = get_settings()
    payload: dict[str, Any] = {
        "session": {
            "type": "realtime",
            "model": OPENAI_REALTIME_MODEL,
            "instructions": text_prompt,
            # GA does not accept ["audio", "text"]; per the schema, ["audio"] already produces audio + a text transcript.
            "output_modalities": ["audio"],
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    # Server-side VAD with explicit interrupt + auto-respond. Without this set explicitly, OpenAI applied defaults that left interrupt_response=false → the AI kept talking over the user.
                    "turn_detection": {
                        "type": "server_vad",
                        "interrupt_response": True,
                        "create_response": True,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "voice": voice_id,
                },
            },
        },
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    if http_client is None:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                OPENAI_CLIENT_SECRETS_URL, json=payload, headers=headers
            )
    else:
        response = await http_client.post(
            OPENAI_CLIENT_SECRETS_URL, json=payload, headers=headers
        )

    if response.status_code >= 400:
        logger.error(
            "OpenAI client_secrets %s voice_id=%s body=%s",
            response.status_code,
            voice_id,
            response.text,
        )
    response.raise_for_status()
    body = response.json()
    token = body.get("value")
    if not isinstance(token, str) or not token:
        raise RuntimeError(
            "OpenAI client_secrets response missing top-level 'value' field"
        )

    return OpenAISession(
        ws_url=OPENAI_REALTIME_WS_URL,
        ephemeral_token=token,
        voice_id=voice_id,
    )
