"""extract_mistakes: orchestrates the LLM call + normalization."""

from typing import Any

import httpx
import pytest

from app.pipelines.mistake_detection import extract_mistakes as extract_mistakes_mod
from app.pipelines.mistake_detection.extract_mistakes import extract_mistakes


async def _fake_complete(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    return {
        "mistakes": [
            {"original": "I am agree", "corrected": "I agree", "category": "tense"},
            {"original": "junk", "corrected": "junk", "category": "naturalness"},
        ]
    }


async def _empty_complete(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    return {}


async def _raises_complete(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    raise httpx.HTTPError("upstream timeout")


async def test_extract_mistakes_returns_empty_on_no_texts() -> None:
    assert await extract_mistakes([]) == []


async def test_extract_mistakes_runs_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(extract_mistakes_mod, "complete_json", _fake_complete)
    out = await extract_mistakes(["hello"])
    assert len(out) == 1
    assert out[0].original == "I am agree"


async def test_extract_mistakes_empty_when_llm_returns_blank(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(extract_mistakes_mod, "complete_json", _empty_complete)
    assert await extract_mistakes(["hi"]) == []


async def test_extract_mistakes_empty_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(extract_mistakes_mod, "complete_json", _raises_complete)
    assert await extract_mistakes(["hi"]) == []
