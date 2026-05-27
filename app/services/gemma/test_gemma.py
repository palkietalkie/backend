"""Google Gemma wrapper tests. httpx is mocked via respx."""

from typing import Any

import httpx
import pytest
import respx

from app.config import Settings
from app.services.gemma.complete_json import complete_json
from app.services.gemma.complete_text import complete_text
from app.services.gemma.constants import DEFAULT_MODEL

GEMMA_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/{DEFAULT_MODEL}:generateContent"
)


def _gemma_response(text: str) -> dict[str, Any]:
    return {"candidates": [{"content": {"parts": [{"text": text}]}}]}


@respx.mock
async def test_complete_text_happy_path(settings: Settings) -> None:
    route = respx.post(GEMMA_URL).mock(
        return_value=httpx.Response(200, json=_gemma_response("hi from gemma"))
    )
    out = await complete_text("Say hi", system="You are a tutor.", max_tokens=64)
    assert out == "hi from gemma"
    assert route.called
    # Body shape: contents[0].parts[0].text is the prompt + system. CallList isn't parameterized so use .last (typed as Call).
    call = route.calls.last
    body = call.request.read().decode()
    assert "Say hi" in body
    assert "You are a tutor." in body


@respx.mock
async def test_complete_text_concatenates_multiple_parts(settings: Settings) -> None:
    payload: dict[str, Any] = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "part1 "}, {"text": "part2"}],
                }
            }
        ]
    }
    respx.post(GEMMA_URL).mock(return_value=httpx.Response(200, json=payload))
    assert await complete_text("p") == "part1 part2"


@respx.mock
async def test_complete_text_empty_on_missing_candidates(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(return_value=httpx.Response(200, json={"candidates": []}))
    assert await complete_text("p") == ""


async def test_complete_text_empty_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from app.config import get_settings

    get_settings.cache_clear()
    try:
        assert await complete_text("hello") == ""
    finally:
        get_settings.cache_clear()


@respx.mock
async def test_complete_json_parses_plain_json(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(
        return_value=httpx.Response(200, json=_gemma_response('{"foo": "bar"}'))
    )
    out = await complete_json("p")
    assert out == {"foo": "bar"}


@respx.mock
async def test_complete_json_strips_markdown_fences(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(
        return_value=httpx.Response(200, json=_gemma_response('```json\n{"foo": 1}\n```'))
    )
    out = await complete_json("p")
    assert out == {"foo": 1}


@respx.mock
async def test_complete_json_extracts_first_balanced_object(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(
        return_value=httpx.Response(
            200,
            json=_gemma_response('prose before {"k": "v"} prose after'),
        )
    )
    out = await complete_json("p")
    assert out == {"k": "v"}


@respx.mock
async def test_complete_json_returns_empty_on_parse_failure(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(return_value=httpx.Response(200, json=_gemma_response("not json")))
    out = await complete_json("p")
    assert out == {}


@respx.mock
async def test_complete_text_raises_on_http_error(settings: Settings) -> None:
    respx.post(GEMMA_URL).mock(return_value=httpx.Response(500, text="boom"))
    with pytest.raises(httpx.HTTPStatusError):
        await complete_text("p")
