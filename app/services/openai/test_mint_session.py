"""OpenAI Realtime session minter tests.

Mocks ``httpx.AsyncClient.post`` so no real OpenAI calls are made. Focused on the
contract we depend on: GA endpoint URL, payload shape, voice-id validation, and
top-level ``value`` extraction.
"""

from typing import Any

import httpx
import pytest

from app.services.openai.constants import (
    OPENAI_CLIENT_SECRETS_URL,
    OPENAI_REALTIME_MODEL,
    OPENAI_REALTIME_WS_URL,
    OpenAIVoiceId,
)
from app.services.openai.mint_session import mint_openai_session


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


class _FakeResponse:
    def __init__(self, status_code: int, json_body: dict[str, Any]) -> None:
        self.status_code = status_code
        self._json_body = json_body
        self.text = ""

    def json(self) -> dict[str, Any]:
        return self._json_body

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                "fake",
                request=httpx.Request("POST", OPENAI_CLIENT_SECRETS_URL),
                response=httpx.Response(self.status_code),
            )


class _FakeClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, Any], dict[str, str]]] = []

    async def post(
        self, url: str, *, json: dict[str, Any], headers: dict[str, str]
    ) -> _FakeResponse:
        self.calls.append((url, json, headers))
        return self.response


@pytest.mark.asyncio
async def test_mint_extracts_token_from_top_level_value() -> None:
    # Regression: Beta response nested the token under ``client_secret.value``; GA returns it at top-level ``value``. Pulling from the wrong key silently produced ``RuntimeError: missing client_secret.value`` before the fix.
    fake = _FakeClient(
        _FakeResponse(200, {"value": "ek_abc123", "expires_at": 1234567890, "session": {}})
    )
    session = await mint_openai_session(
        text_prompt="be a real person",
        voice_id=OpenAIVoiceId.ASH,
        http_client=fake,  # type: ignore[arg-type]
    )
    assert session.ws_url == OPENAI_REALTIME_WS_URL
    assert session.ephemeral_token == "ek_abc123"
    assert session.voice_id == OpenAIVoiceId.ASH


@pytest.mark.asyncio
async def test_mint_sends_ga_payload_shape() -> None:
    # Regression: Beta payload was flat (modalities, voice, input_audio_format at top level). GA wraps everything under ``session`` with ``type: "realtime"``, ``output_modalities`` (not ``modalities``), and audio formats as objects ({"type": "audio/pcm", "rate": 24000}) instead of strings ("pcm16").
    fake = _FakeClient(_FakeResponse(200, {"value": "ek_tok"}))
    await mint_openai_session(
        text_prompt="hello prompt",
        voice_id=OpenAIVoiceId.SHIMMER,
        http_client=fake,  # type: ignore[arg-type]
    )
    assert len(fake.calls) == 1
    url, body, headers = fake.calls[0]
    assert url == OPENAI_CLIENT_SECRETS_URL
    session = body["session"]
    assert session["type"] == "realtime"
    assert session["model"] == OPENAI_REALTIME_MODEL
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
    fake = _FakeClient(_FakeResponse(200, {"session": {}}))
    with pytest.raises(RuntimeError, match="'value'"):
        await mint_openai_session(
            text_prompt="x",
            voice_id=OpenAIVoiceId.ASH,
            http_client=fake,  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_mint_raises_http_error_on_non_2xx() -> None:
    fake = _FakeClient(_FakeResponse(401, {"error": "unauthorized"}))
    with pytest.raises(httpx.HTTPStatusError):
        await mint_openai_session(
            text_prompt="x",
            voice_id=OpenAIVoiceId.ASH,
            http_client=fake,  # type: ignore[arg-type]
        )
