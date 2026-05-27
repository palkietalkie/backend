from typing import Any

from app.pipelines.kg_extraction.parse_payload import parse_payload
from app.services.neo4j.models import KGEntity, KGRelation


def test_parse_payload_clean_input() -> None:
    payload: dict[str, Any] = {
        "entities": [
            {"type": "person", "name": "Alice", "props": {"city": "Paris"}},
            {"type": "place", "name": "Paris", "props": {}},
        ],
        "relations": [
            {"src": "Alice", "relation": "LIVES_IN", "dst": "Paris"},
        ],
    }
    entities, relations = parse_payload(payload)
    assert entities == [
        KGEntity(type="person", name="Alice", props={"city": "Paris"}),
        KGEntity(type="place", name="Paris", props={}),
    ]
    assert relations == [KGRelation(src_name="Alice", relation="LIVES_IN", dst_name="Paris")]


def test_parse_payload_drops_malformed_entities() -> None:
    payload: dict[str, Any] = {
        "entities": [
            "not-a-dict",
            {"type": "person", "name": ""},
            {"type": "person", "name": "  "},
            {"name": "Bob"},
            {"type": 42, "name": "X"},
            {"type": "person", "name": "Valid"},
        ],
        "relations": [],
    }
    entities, _ = parse_payload(payload)
    assert [e.name for e in entities] == ["Valid"]


def test_parse_payload_filters_non_scalar_props() -> None:
    payload: dict[str, Any] = {
        "entities": [
            {
                "type": "person",
                "name": "A",
                "props": {
                    "age": 30,
                    "name": "Alice",
                    "extra": [1, 2],
                    "obj": {"k": "v"},
                },
            }
        ],
        "relations": [],
    }
    [e], _ = parse_payload(payload)
    assert e.props == {"age": 30, "name": "Alice"}


def test_parse_payload_drops_malformed_relations() -> None:
    payload: dict[str, Any] = {
        "entities": [],
        "relations": [
            "not-a-dict",
            {"src": "A", "dst": "B"},
            {"src": 1, "relation": "R", "dst": "B"},
            {"src": "A", "relation": "KNOWS", "dst": "B"},
        ],
    }
    _, relations = parse_payload(payload)
    assert relations == [KGRelation(src_name="A", relation="KNOWS", dst_name="B")]


def test_parse_payload_empty_input() -> None:
    entities, relations = parse_payload({})
    assert entities == []
    assert relations == []
