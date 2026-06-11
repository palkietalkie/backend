import uuid
from typing import Any

import pytest

from app.services.pinecone import upsert_transcript_chunks as mod
from app.services.pinecone.upsert_transcript_chunks import upsert_transcript_chunks


class _FakeIndex:
    def __init__(self) -> None:
        self.upserts: list[tuple[str, list[dict[str, Any]]]] = []

    def upsert_records(self, *, namespace: str, records: list[dict[str, Any]]) -> None:
        self.upserts.append((namespace, records))


async def test_upsert_builds_one_record_per_chunk(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeIndex()
    monkeypatch.setattr(mod, "get_memory_index", lambda: fake)
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()

    await upsert_transcript_chunks(user_id, session_id, ["first chunk", "second chunk"])

    namespace, records = fake.upserts[0]
    assert namespace == str(user_id)
    assert [r["_id"] for r in records] == [f"{session_id}:0", f"{session_id}:1"]
    assert records[0]["text"] == "first chunk"
    assert records[1]["session_id"] == str(session_id)


async def test_upsert_is_noop_on_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeIndex()
    monkeypatch.setattr(mod, "get_memory_index", lambda: fake)
    await upsert_transcript_chunks(uuid.uuid4(), uuid.uuid4(), [])
    assert fake.upserts == []
