import uuid

from app.services.neo4j import upsert_kg as upsert_kg_mod
from app.services.neo4j._fakes import FakeDriver
from app.services.neo4j.models import KGEntity, KGRelation
from app.services.neo4j.upsert_kg import upsert_kg


async def test_upsert_kg_runs_one_query_per_entity_plus_relation(monkeypatch) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_driver", lambda: fake)
    user_id = uuid.uuid4()
    entities = [
        KGEntity(type="person", name="Alice", props={}),
        KGEntity(type="place", name="Paris", props={"country": "FR"}),
    ]
    relations = [KGRelation(src_name="Alice", relation="LIVES IN", dst_name="Paris")]
    await upsert_kg(user_id, entities, relations)
    assert len(fake.fake_session.queries) == 3
    # Relation type must be uppercased + non-alnum replaced with underscore.
    last_query = fake.fake_session.queries[-1][0]
    assert ":LIVES_IN" in last_query


async def test_upsert_kg_sanitizes_empty_relation(monkeypatch) -> None:
    fake = FakeDriver()
    monkeypatch.setattr(upsert_kg_mod, "get_driver", lambda: fake)
    entities = [KGEntity(type="person", name="A", props={})]
    relations = [KGRelation(src_name="A", relation="", dst_name="A")]
    await upsert_kg(uuid.uuid4(), entities, relations)
    rel_query = fake.fake_session.queries[-1][0]
    assert ":RELATED" in rel_query
