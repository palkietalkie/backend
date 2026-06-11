import uuid

import pytest

from app.services.neo4j import upsert_kg as upsert_kg_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.models import KGEntity, KGRelation
from app.services.neo4j.upsert_kg import upsert_kg


async def test_upsert_kg_runs_one_query_per_entity_plus_relation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    user_id = uuid.uuid4()
    entities = [
        KGEntity(type="person", name="Alice", props={}),
        KGEntity(type="place", name="Paris", props={"country": "FR"}),
    ]
    relations = [KGRelation(src_name="Alice", relation="LIVES IN", dst_name="Paris")]
    await upsert_kg(user_id, entities, relations)
    assert len(fake.fake_session.queries) == 3
    # All edges share the :RELATED Cypher type; the LLM-supplied label is uppercased + non-alnum replaced with underscore and stored as `kind`.
    last_query, last_params = fake.fake_session.queries[-1]
    assert ":RELATED" in last_query
    assert last_params["kind"] == "LIVES_IN"


async def test_upsert_kg_sanitizes_empty_relation(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    entities = [KGEntity(type="person", name="A", props={})]
    relations = [KGRelation(src_name="A", relation="", dst_name="A")]
    await upsert_kg(uuid.uuid4(), entities, relations)
    last_query, last_params = fake.fake_session.queries[-1]
    assert ":RELATED" in last_query
    assert last_params["kind"] == "RELATED"
