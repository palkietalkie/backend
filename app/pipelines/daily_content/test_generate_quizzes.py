"""Tests for generate_quizzes — Gemma call is stubbed."""

from typing import Any

import httpx
import pytest

from app.pipelines.daily_content import generate_quizzes as mod


async def test_generate_quizzes_returns_items(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(_prompt: str) -> dict[str, Any]:
        return {
            "items": [
                {"question": "Why?", "answer": "Because."},
                {"question": "How?", "answer": "Like this."},
            ]
        }

    monkeypatch.setattr(mod, "complete_json", _fake)
    items = await mod.generate_quizzes(["news 1", "news 2"])
    assert len(items) == 2
    assert items[0].title == "Why?"
    assert items[0].summary == "Because."
    assert items[0].source == ""
    assert items[0].image_url == ""


async def test_generate_quizzes_caps_at_10(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(_prompt: str) -> dict[str, Any]:
        return {"items": [{"question": f"q{i}", "answer": f"a{i}"} for i in range(20)]}

    monkeypatch.setattr(mod, "complete_json", _fake)
    items = await mod.generate_quizzes([])
    assert len(items) == 10


async def test_generate_quizzes_empty_on_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raises(_prompt: str) -> dict[str, Any]:
        raise httpx.HTTPError("boom")

    monkeypatch.setattr(mod, "complete_json", _raises)
    assert await mod.generate_quizzes([]) == []


async def test_generate_quizzes_empty_on_empty_data(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _empty(_prompt: str) -> dict[str, Any]:
        return {}

    monkeypatch.setattr(mod, "complete_json", _empty)
    assert await mod.generate_quizzes([]) == []


async def test_generate_quizzes_empty_on_bad_shape(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _bad(_prompt: str) -> dict[str, Any]:
        return {"items": [{"missing_fields": True}]}

    monkeypatch.setattr(mod, "complete_json", _bad)
    assert await mod.generate_quizzes([]) == []
