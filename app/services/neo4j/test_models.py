from app.services.neo4j.models import KGEntity, KGRelation


def test_kg_entity_kg_relation_dataclasses() -> None:
    entity = KGEntity(type="person", name="Alice", props={"age": 30})
    relation = KGRelation(src_name="Alice", relation="KNOWS", dst_name="Bob")
    assert entity.name == "Alice"
    assert entity.props["age"] == 30
    assert relation.src_name == "Alice"
    assert relation.relation == "KNOWS"
    assert relation.dst_name == "Bob"
