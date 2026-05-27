import uuid

import pytest

from app.services.neo4j import fetch_kg as fetch_kg_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.fetch_kg import fetch_kg


async def test_fetch_kg_normalizes_records(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDriver()
    fake.fake_session.enqueue([{"name": "Alice", "type": "person", "props": {"age": 30}}])
    fake.fake_session.enqueue([{"src": "Alice", "rel": "KNOWS", "dst": "Bob"}])
    monkeypatch.setattr(fetch_kg_mod, "get_driver", lambda: fake)

    out = await fetch_kg(uuid.uuid4())
    assert out["nodes"] == [{"name": "Alice", "type": "person", "props": {"age": 30}}]
    assert out["edges"] == [{"src": "Alice", "rel": "KNOWS", "dst": "Bob"}]
