"""filter_phrases_with_llm: degrades to "keep everything" on outage / empty input."""

from typing import Any

import httpx
import pytest

from app.post_session_nlp.phrase_extraction import filter_phrases_with_llm as filter_mod
from app.post_session_nlp.phrase_extraction.filter_phrases_with_llm import filter_phrases_with_llm


async def _keep_subset(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    return {"keep": ["fancy idiom", "phrasal verb"]}


async def _malformed(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    return {"keep": "not-a-list"}


async def _raises(_prompt: str, **_kwargs: Any) -> dict[str, Any]:
    raise httpx.HTTPError("upstream down")


async def test_filter_returns_empty_on_no_candidates() -> None:
    assert await filter_phrases_with_llm([]) == []


async def test_filter_keeps_llm_subset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(filter_mod, "complete_json", _keep_subset)
    out = await filter_phrases_with_llm(["fancy idiom", "phrasal verb", "boring phrase"])
    assert out == ["fancy idiom", "phrasal verb"]


async def test_filter_returns_empty_on_validation_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(filter_mod, "complete_json", _malformed)
    assert await filter_phrases_with_llm(["x"]) == []


async def test_filter_returns_candidates_unchanged_on_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(filter_mod, "complete_json", _raises)
    out = await filter_phrases_with_llm(["a", "b"])
    assert out == ["a", "b"]
