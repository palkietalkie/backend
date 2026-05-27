from typing import Any

from app.services.neo4j.models import KGEntity, KGRelation


def parse_payload(data: dict[str, Any]) -> tuple[list[KGEntity], list[KGRelation]]:
    entities: list[KGEntity] = []
    for e in data.get("entities") or []:
        if not isinstance(e, dict):
            continue
        etype = e.get("type")
        name = e.get("name")
        if not (isinstance(etype, str) and isinstance(name, str) and name.strip()):
            continue
        props_raw = e.get("props") or {}
        props = {
            k: v
            for k, v in props_raw.items()
            if isinstance(k, str) and isinstance(v, (str, int))
        }
        entities.append(KGEntity(type=etype, name=name.strip(), props=props))

    relations: list[KGRelation] = []
    for r in data.get("relations") or []:
        if not isinstance(r, dict):
            continue
        src = r.get("src")
        dst = r.get("dst")
        rel = r.get("relation")
        if not (isinstance(src, str) and isinstance(dst, str) and isinstance(rel, str)):
            continue
        relations.append(
            KGRelation(src_name=src.strip(), relation=rel.strip(), dst_name=dst.strip())
        )
    return entities, relations
