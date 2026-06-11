import uuid
from typing import Any

import pytest

from app.services.pinecone import query_transcript_memory as mod
from app.services.pinecone.query_transcript_memory import query_transcript_memory


class _FakeIndex:
    def __init__(self, result: dict[str, Any]) -> None:
        self.result = result

    def search(self, *, namespace: str, query: dict[str, Any]) -> dict[str, Any]:
        return self.result


async def test_query_returns_chunk_texts(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeIndex(
        {"result": {"hits": [{"fields": {"text": "hello"}}, {"fields": {"text": "world"}}]}}
    )
    monkeypatch.setattr(mod, "get_memory_index", lambda: fake)
    out = await query_transcript_memory(uuid.uuid4(), "q")
    assert out == ["hello", "world"]


async def test_query_empty_when_no_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeIndex({"result": {"hits": []}})
    monkeypatch.setattr(mod, "get_memory_index", lambda: fake)
    out = await query_transcript_memory(uuid.uuid4(), "q")
    assert out == []
