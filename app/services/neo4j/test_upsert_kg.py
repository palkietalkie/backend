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


async def test_self_entity_folds_onto_user_node_not_an_entity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The speaker's own attributes must land on the canonical User node, never an :Entity copy.
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    entities = [KGEntity(type="person", name="__SELF__", props={"current_weight": "85kg"})]
    await upsert_kg(uuid.uuid4(), entities, [])
    assert len(fake.fake_session.queries) == 1
    query, params = fake.fake_session.queries[0]
    assert "SET u += $props" in query
    assert "Entity" not in query
    assert params["props"] == {"current_weight": "85kg"}


@pytest.mark.parametrize("alias", ["user", "User", "me", "I", "the user", "  Myself "])
async def test_self_aliases_all_resolve_to_user_node(
    monkeypatch: pytest.MonkeyPatch, alias: str
) -> None:
    # Defense in depth: even if the LLM ignores "__SELF__" and writes "user"/"User"/"me", it must not become an Entity.
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    await upsert_kg(uuid.uuid4(), [KGEntity(type="person", name=alias, props={})], [])
    query, _ = fake.fake_session.queries[0]
    assert "Entity" not in query


async def test_self_relation_connects_user_to_entity(monkeypatch: pytest.MonkeyPatch) -> None:
    # "__SELF__ PLAYS Tennis" → (User)-[:RELATED {kind:PLAYS}]->(Entity Tennis), not an Entity-Entity edge.
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    entities = [KGEntity(type="interest", name="Tennis", props={})]
    relations = [KGRelation(src_name="__SELF__", relation="PLAYS", dst_name="Tennis")]
    await upsert_kg(uuid.uuid4(), entities, relations)
    query, params = fake.fake_session.queries[-1]
    assert "(u)-[r:RELATED]->(b)" in query
    assert "MERGE (u:User {id: $uid})" in query
    assert params["dst"] == "Tennis"
    assert params["kind"] == "PLAYS"
    assert "src" not in params


async def test_entity_under_users_real_name_folds_onto_user_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # If the LLM ignores the prompt and emits the speaker by their actual name, user_name catches it.
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    entities = [KGEntity(type="person", name="Wes", props={"goal_weight": "59kg"})]
    await upsert_kg(uuid.uuid4(), entities, [], user_name="Wes")
    query, params = fake.fake_session.queries[0]
    assert "SET u += $props" in query
    assert "Entity" not in query
    assert params["props"] == {"goal_weight": "59kg"}


async def test_self_to_self_relation_is_skipped(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_neo4j_driver", lambda: fake)
    relations = [KGRelation(src_name="__SELF__", relation="IS", dst_name="me")]
    await upsert_kg(uuid.uuid4(), [], relations)
    assert fake.fake_session.queries == []
