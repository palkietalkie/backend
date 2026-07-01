"""OpenAI Realtime API session minter (GA, not Beta).

Alternative inference path to PersonaPlex. Backend calls OpenAI's GA endpoint ``/v1/realtime/client_secrets`` to mint a short-lived ephemeral token (default 10 min TTL, configurable up to 2h), which iOS uses to open a WebSocket directly to ``wss://api.openai.com/v1/realtime?model=gpt-realtime-2``. The audio + text protocol on that WS is JSON event frames (``input_audio_buffer.append`` going out, ``response.audio.delta`` coming back), NOT the binary Ogg-Opus protocol the PersonaPlex path speaks. iOS picks the wire format based on the ``provider`` field on ``StartResponse``.

This used to call the Beta endpoint ``/v1/realtime/sessions`` with the ``OpenAI-Beta: realtime=v1`` header; OpenAI killed the Beta shape entirely (``beta_api_shape_disabled``) so the GA contract is the only path now. Source of truth for the GA shape: openai/openai-python ``src/openai/resources/realtime/`` and ``src/openai/types/realtime/*``."""

import logging
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.config import get_settings
from app.profile.tutor_speaking_speed import TUTOR_SPEED_PLAYBACK_RATE, TutorSpeakingSpeed
from app.services.openai.constants import (
    OPENAI_CLIENT_SECRETS_URL,
    OPENAI_REALTIME_MODEL_PAID,
    OPENAI_REALTIME_WS_URL_TEMPLATE,
    OPENAI_TRANSCRIPTION_DELAY,
    OPENAI_TRANSCRIPTION_MODEL,
    OpenAIVoiceId,
)
from app.services.openai.realtime_tools import REALTIME_TOOLS

logger = logging.getLogger(__name__)


class HTTPPoster(Protocol):
    """Structural type covering both httpx.AsyncClient.post and the in-test FakeClient — only the kwargs we actually use."""

    async def post(
        self, url: str, *, json: dict[str, Any], headers: dict[str, str]
    ) -> httpx.Response: ...


@dataclass(frozen=True)
class OpenAISession:
    ws_url: str
    ephemeral_token: str
    voice_id: OpenAIVoiceId
    # The realtime model this session runs on, stored per session so cost analysis survives a future tier split (e.g. free → mini, paid → full).
    model: str


async def mint_openai_session(
    text_prompt: str,
    voice_id: OpenAIVoiceId,
    *,
    speaking_speed: TutorSpeakingSpeed = "normal",
    http_client: HTTPPoster | None = None,
) -> OpenAISession:
    settings = get_settings()
    # Always the full realtime model, regardless of tier. The mini tier ignores the prompt's explicit ban on patient-tutor filler and parrots "let's slow down" nearly every turn (confirmed in prod transcripts, even while acknowledging it overuses the phrase), which wrecks the conversation. Conversation quality IS the product, so the free-tier cost increase is accepted.
    realtime_model = OPENAI_REALTIME_MODEL_PAID
    ws_url = OPENAI_REALTIME_WS_URL_TEMPLATE.format(model=realtime_model)
    payload: dict[str, Any] = {
        "session": {
            "type": "realtime",
            "model": realtime_model,
            "instructions": text_prompt,
            # GA does not accept ["audio", "text"]; per the schema, ["audio"] already produces audio + a text transcript.
            "output_modalities": ["audio"],
            "tools": REALTIME_TOOLS,
            "tool_choice": "auto",
            "audio": {
                "input": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "turn_detection": {
                        # Semantic VAD over pure energy threshold: it judges whether the audio is a plausibly-complete user utterance rather than firing on any sound above a level, which gives cleaner turn-taking.
                        "type": "semantic_vad",
                        # `eagerness="auto"` keeps turn-taking snappy (low adds a real wait before committing, hurting the quiet-environment case and barge-in). Outdoor ambient-noise robustness lives upstream in the iOS near-field gate (Audio/NearFieldGate.swift), which silences anything that isn't the close primary speaker before it reaches this VAD, so the VAD doesn't need to be conservative to avoid phantom turns. Tighten this only if on-device testing shows the gate leaking noise into committed turns.
                        "eagerness": "auto",
                        "interrupt_response": True,
                        "create_response": True,
                    },
                    # Without this the API never emits `conversation.item.input_audio_transcription.completed`, iOS never sees user turns, and the transcripts table only ever has persona rows.
                    "transcription": {
                        "model": OPENAI_TRANSCRIPTION_MODEL,
                        "delay": OPENAI_TRANSCRIPTION_DELAY,
                    },
                },
                "output": {
                    "format": {"type": "audio/pcm", "rate": 24000},
                    "voice": voice_id,
                    # Real post-processing slowdown of the generated audio (0.25-1.5, 1.0 = natural), so a beginner who set "slow" actually hears slower speech instead of just a prompt the model ignores. The prompt hint in assemble_prompt shapes cadence on top of this.
                    "speed": TUTOR_SPEED_PLAYBACK_RATE[speaking_speed],
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
            response = await client.post(OPENAI_CLIENT_SECRETS_URL, json=payload, headers=headers)
    else:
        response = await http_client.post(OPENAI_CLIENT_SECRETS_URL, json=payload, headers=headers)

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
        raise RuntimeError("OpenAI client_secrets response missing top-level 'value' field")

    return OpenAISession(
        ws_url=ws_url,
        ephemeral_token=token,
        voice_id=voice_id,
        model=realtime_model,
    )
