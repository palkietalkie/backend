import uuid

import pytest

from app.services.neo4j import search_entities as mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.search_entities import search_entities


async def test_search_entities_zips_parallel_rel_and_target_lists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeDriver()
    # The query returns rels + targets as two parallel scalar lists (null rows already dropped in Cypher); the function zips them into {rel, target} dicts.
    fake.fake_session.enqueue(
        [{"name": "Naoto", "type": "person", "rels": ["WORKS_AT"], "targets": ["Kawasaki"]}]
    )
    monkeypatch.setattr(mod, "get_neo4j_driver", lambda: fake)

    out = await search_entities(uuid.uuid4(), "nao")
    assert out == [
        {
            "name": "Naoto",
            "type": "person",
            "relations": [{"rel": "WORKS_AT", "target": "Kawasaki"}],
        }
    ]


async def test_search_entities_handles_entity_with_no_relations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeDriver()
    fake.fake_session.enqueue([{"name": "Solo", "type": "person", "rels": [], "targets": []}])
    monkeypatch.setattr(mod, "get_neo4j_driver", lambda: fake)

    out = await search_entities(uuid.uuid4(), "solo")
    assert out == [{"name": "Solo", "type": "person", "relations": []}]
