"""OpenAI Realtime session minter tests.

Mocks ``httpx.AsyncClient.post`` so no real OpenAI calls are made. Focused on the contract we depend on: GA endpoint URL, payload shape, voice-id validation, and top-level ``value`` extraction."""

from typing import Any

import httpx
import pytest

from app.profile.tutor_speaking_speed import TUTOR_SPEED_PLAYBACK_RATE
from app.services.openai.constants import (
    OPENAI_CLIENT_SECRETS_URL,
    OPENAI_REALTIME_MODEL_PAID,
    OPENAI_REALTIME_WS_URL_TEMPLATE,
    OpenAIVoiceId,
)
from app.services.openai.mint_openai_session import mint_openai_session


def test_voice_enum_includes_known_ids() -> None:
    members = {v.value for v in OpenAIVoiceId}
    assert members == {
        "alloy",
        "ash",
        "ballad",
        "cedar",
        "coral",
        "echo",
        "marin",
        "sage",
        "shimmer",
        "verse",
    }


def test_endpoint_url_is_ga_client_secrets_not_beta_sessions() -> None:
    # Regression: the Beta endpoint /v1/realtime/sessions returns 400 beta_api_shape_disabled. GA endpoint is /v1/realtime/client_secrets.
    assert OPENAI_CLIENT_SECRETS_URL == "https://api.openai.com/v1/realtime/client_secrets"


@pytest.mark.asyncio
async def test_session_registers_recall_tools() -> None:
    # The realtime model can only call recall mid-conversation if the tools are in the minted session config.
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(text_prompt="x", voice_id=OpenAIVoiceId.ASH, http_client=fake)
    _url, body, _headers = fake.calls[0]
    tools = body["session"]["tools"]
    names = {t["name"] for t in tools}
    assert names == {
        "recall_facts",
        "recall_past_conversations",
        "search_transcripts",
        "end_conversation",
        "web_fetch",
    }
    assert body["session"]["tool_choice"] == "auto"
    for tool in tools:
        assert tool["type"] == "function"
        props = tool["parameters"]["properties"]
        if tool["name"] == "end_conversation":
            assert props == {}  # pure signal, no parameters
        elif tool["name"] == "web_fetch":
            assert "url" in props
        else:
            assert "query" in props  # recall tools


@pytest.mark.asyncio
async def test_turn_detection_uses_auto_eagerness_semantic_vad() -> None:
    # Turn-taking stays snappy at eagerness="auto"; outdoor noise robustness lives in the iOS near-field gate upstream, not in a conservative VAD. semantic_vad (not server_vad) is the regression guard here — server_vad would fire on any energy and reintroduce phantom turns.
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(text_prompt="x", voice_id=OpenAIVoiceId.ASH, http_client=fake)
    _url, body, _headers = fake.calls[0]
    turn_detection = body["session"]["audio"]["input"]["turn_detection"]
    assert turn_detection["type"] == "semantic_vad"
    assert turn_detection["eagerness"] == "auto"


@pytest.mark.asyncio
async def test_paid_users_get_full_realtime_and_transcription_models() -> None:
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(
        text_prompt="x",
        voice_id=OpenAIVoiceId.ASH,
        is_premium=True,
        http_client=fake,
    )
    _url, body, _headers = fake.calls[0]
    assert body["session"]["model"] == OPENAI_REALTIME_MODEL_PAID
    assert body["session"]["audio"]["input"]["transcription"]["model"] == "gpt-4o-transcribe"


@pytest.mark.asyncio
async def test_free_users_get_full_realtime_but_mini_transcription() -> None:
    # The realtime model is ALWAYS the full one (mini parrots "let's slow down" and ignores prompt prohibitions). Only transcription stays tiered to save cost on the free plan.
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    session = await mint_openai_session(
        text_prompt="x",
        voice_id=OpenAIVoiceId.ASH,
        is_premium=False,
        http_client=fake,
    )
    _url, body, _headers = fake.calls[0]
    assert body["session"]["model"] == OPENAI_REALTIME_MODEL_PAID
    assert body["session"]["audio"]["input"]["transcription"]["model"] == "gpt-4o-mini-transcribe"
    assert session.ws_url.endswith(f"model={OPENAI_REALTIME_MODEL_PAID}")


@pytest.mark.asyncio
async def test_session_records_realtime_model_matching_ws_url() -> None:
    # The session carries its model id so per-session cost analysis can attribute spend; it must be the SAME model the ws_url connects to, or the recorded model lies about what actually ran.
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    session = await mint_openai_session(
        text_prompt="x",
        voice_id=OpenAIVoiceId.ASH,
        http_client=fake,
    )
    assert session.model == OPENAI_REALTIME_MODEL_PAID
    assert session.ws_url.endswith(f"model={session.model}")


@pytest.mark.asyncio
async def test_session_sets_output_speed_from_speaking_speed() -> None:
    # A beginner's "very_slow" must reach the API as a real audio.output.speed (post-processing slowdown), not just a prompt hint the model can drift away from.
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(
        text_prompt="x",
        voice_id=OpenAIVoiceId.ASH,
        speaking_speed="very_slow",
        http_client=fake,
    )
    _u, body, _h = fake.calls[0]
    assert body["session"]["audio"]["output"]["speed"] == TUTOR_SPEED_PLAYBACK_RATE["very_slow"]


@pytest.mark.asyncio
async def test_session_default_speed_is_natural() -> None:
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(text_prompt="x", voice_id=OpenAIVoiceId.ASH, http_client=fake)
    _u, body, _h = fake.calls[0]
    assert body["session"]["audio"]["output"]["speed"] == 1.0


class _FakeClient:
    """Implements the HTTPPoster Protocol from mint_session.py — only the kwargs we use."""

    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    async def post(
        self, url: str, *, json: dict[str, Any], headers: dict[str, str]
    ) -> httpx.Response:
        self.calls.append((url, json, headers))
        return self.response


def _resp(status_code: int, body: dict[str, Any]) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=body,
        request=httpx.Request("POST", OPENAI_CLIENT_SECRETS_URL),
    )


@pytest.mark.asyncio
async def test_mint_extracts_token_from_top_level_value() -> None:
    # Regression: Beta response nested the token under ``client_secret.value``; GA returns it at top-level ``value``. Pulling from the wrong key silently produced ``RuntimeError: missing client_secret.value`` before the fix.
    fake = _FakeClient(_resp(200, {"value": "ek_abc123", "expires_at": 1234567890, "session": {}}))
    session = await mint_openai_session(
        text_prompt="be a real person",
        voice_id=OpenAIVoiceId.ASH,
        http_client=fake,
    )
    assert session.ws_url == OPENAI_REALTIME_WS_URL_TEMPLATE.format(
        model=OPENAI_REALTIME_MODEL_PAID
    )
    assert session.ephemeral_token == "ek_abc123"
    assert session.voice_id == OpenAIVoiceId.ASH


@pytest.mark.asyncio
async def test_mint_sends_ga_payload_shape() -> None:
    # Regression: Beta payload was flat (modalities, voice, input_audio_format at top level). GA wraps everything under ``session`` with ``type: "realtime"``, ``output_modalities`` (not ``modalities``), and audio formats as objects ({"type": "audio/pcm", "rate": 24000}) instead of strings ("pcm16").
    fake = _FakeClient(_resp(200, {"value": "ek_tok"}))
    await mint_openai_session(
        text_prompt="hello prompt",
        voice_id=OpenAIVoiceId.SHIMMER,
        http_client=fake,
    )
    assert len(fake.calls) == 1
    url, body, headers = fake.calls[0]
    assert url == OPENAI_CLIENT_SECRETS_URL
    session = body["session"]
    assert session["type"] == "realtime"
    assert session["model"] == OPENAI_REALTIME_MODEL_PAID
    assert session["instructions"] == "hello prompt"
    assert session["output_modalities"] == ["audio"]
    assert session["audio"]["input"]["format"] == {"type": "audio/pcm", "rate": 24000}
    assert session["audio"]["output"]["format"] == {"type": "audio/pcm", "rate": 24000}
    assert session["audio"]["output"]["voice"] == "shimmer"
    assert headers["Authorization"].startswith("Bearer ")
    # OpenAI-Beta header is GONE on GA; sending it doesn't outright break, but the absence proves we cut the Beta dependency.
    assert "OpenAI-Beta" not in headers


@pytest.mark.asyncio
async def test_mint_raises_runtime_error_when_value_missing() -> None:
    fake = _FakeClient(_resp(200, {"session": {}}))
    with pytest.raises(RuntimeError, match="'value'"):
        await mint_openai_session(
            text_prompt="x",
            voice_id=OpenAIVoiceId.ASH,
            http_client=fake,
        )


@pytest.mark.asyncio
async def test_mint_raises_http_error_on_non_2xx() -> None:
    fake = _FakeClient(_resp(401, {"error": "unauthorized"}))
    with pytest.raises(httpx.HTTPStatusError):
        await mint_openai_session(
            text_prompt="x",
            voice_id=OpenAIVoiceId.ASH,
            http_client=fake,
        )
