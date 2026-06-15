"""Tests for the kg_extraction.extract_kg wrapper."""

from typing import Any

import httpx
import pytest

from app.post_session_nlp.kg_extraction import extract_kg as mod


async def test_extract_kg_empty_texts_returns_empty() -> None:
    ents, rels = await mod.extract_kg([])
    assert ents == []
    assert rels == []


async def test_extract_kg_swallows_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _raises(_prompt: str) -> dict[str, Any]:
        raise httpx.HTTPError("upstream gone")

    monkeypatch.setattr(mod, "complete_json", _raises)
    ents, rels = await mod.extract_kg(["I went to Tokyo."])
    assert ents == []
    assert rels == []


async def test_extract_kg_parses_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _fake(_prompt: str) -> dict[str, Any]:
        return {
            "entities": [{"name": "Tokyo", "type": "place"}],
            "relations": [],
        }

    monkeypatch.setattr(mod, "complete_json", _fake)
    ents, _rels = await mod.extract_kg(["Tokyo trip."])
    assert len(ents) == 1
    assert ents[0].name == "Tokyo"
