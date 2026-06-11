import uuid

import pytest

from app.services.neo4j import fetch_kg as fetch_kg_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.fetch_kg import fetch_kg


async def test_fetch_kg_normalizes_records(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDriver()
    # `properties(n)` returns ALL node props including the structural ones (user_id/name/type). attrs must stringify scalar values and drop the structural keys, matching the iOS KGEntityDTO contract (id/type/name/attrs[String:String]).
    fake.fake_session.enqueue(
        [
            {
                "name": "Alice",
                "type": "person",
                "props": {
                    "user_id": "u1",
                    "name": "Alice",
                    "type": "person",
                    "age": 30,
                    "city": "Paris",
                },
            }
        ]
    )
    fake.fake_session.enqueue([{"src": "Alice", "rel": "KNOWS", "dst": "Bob"}])
    monkeypatch.setattr(fetch_kg_mod, "get_neo4j_driver", lambda: fake)

    out = await fetch_kg(uuid.uuid4())
    assert out["nodes"] == [
        {
            "id": "Alice",
            "type": "person",
            "name": "Alice",
            "attrs": {"age": "30", "city": "Paris"},
        }
    ]
    assert out["edges"] == [{"src": "Alice", "rel": "KNOWS", "dst": "Bob"}]
