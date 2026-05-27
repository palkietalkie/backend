from typing import Any

from pydantic import BaseModel, Field, ValidationError

from app.services.neo4j.models import KGEntity, KGRelation


class _EntityIn(BaseModel):
    type: str
    name: str
    # Accept any value type per key; we filter to scalars (str / int) downstream so one bad prop doesn't drop the whole entity.
    props: dict[str, Any] = Field(default_factory=lambda: {})


class _RelationIn(BaseModel):
    src: str
    dst: str
    relation: str


class _PayloadIn(BaseModel):
    # Accept any list element shape; we validate each item individually below so one bad row doesn't drop the whole batch.
    entities: list[Any] = Field(default_factory=lambda: [])
    relations: list[Any] = Field(default_factory=lambda: [])


def parse_payload(data: dict[str, Any]) -> tuple[list[KGEntity], list[KGRelation]]:
    # LLM JSON shape isn't trusted. Validate per-element so a single malformed row doesn't drop the whole batch.
    try:
        parsed = _PayloadIn.model_validate(data)
    except ValidationError:
        return [], []

    entities: list[KGEntity] = []
    for raw in parsed.entities:
        try:
            e = _EntityIn.model_validate(raw)
        except ValidationError:
            continue
        if not e.name.strip():
            continue
        scalar_props: dict[str, str | int] = {
            k: v
            for k, v in e.props.items()
            if isinstance(v, (str, int)) and not isinstance(v, bool)
        }
        entities.append(KGEntity(type=e.type, name=e.name.strip(), props=scalar_props))

    relations: list[KGRelation] = []
    for raw in parsed.relations:
        try:
            r = _RelationIn.model_validate(raw)
        except ValidationError:
            continue
        if r.src.strip() and r.dst.strip() and r.relation.strip():
            relations.append(
                KGRelation(
                    src_name=r.src.strip(), relation=r.relation.strip(), dst_name=r.dst.strip()
                )
            )
    return entities, relations
