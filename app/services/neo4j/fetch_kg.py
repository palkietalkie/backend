import uuid
from typing import Any

from app.services.neo4j.get_neo4j_driver import get_neo4j_driver
from app.services.neo4j.open_session import open_session


async def fetch_kg(user_id: uuid.UUID) -> dict[str, Any]:
    driver = get_neo4j_driver()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    async with open_session(driver) as session:
        result = await session.run(
            "MATCH (n:Entity {user_id: $uid}) WHERE n.removed_at IS NULL "
            "RETURN n.name AS name, n.type AS type, properties(n) AS props",
            uid=str(user_id),
        )
        async for record in result:
            # Wire contract shared with iOS `KGEntityDTO` (id/type/name/attrs). Entities are unique per (user_id, name) via the MERGE in upsert_kg, so `name` is a stable id. attrs are stringified — Neo4j props can be int/float/bool and the iOS DTO decodes `attrs` as [String: String], so anything non-string there would silently break the decode. Keep this shape in sync with ios/.../BackendDTOs.swift KGEntityDTO and its decode test.
            props = dict(record["props"] or {})
            nodes.append(
                {
                    "id": record["name"],
                    "type": record["type"],
                    "name": record["name"],
                    "attrs": {
                        k: str(v)
                        for k, v in props.items()
                        if k not in ("user_id", "name", "type", "removed_at")
                    },
                }
            )

        # The edge type is always :RELATED; the LLM-supplied label lives in `r.kind`.
        # Older rows (from before the schema change) may not have a kind property — coalesce to the edge type so the response is never null.
        result = await session.run(
            "MATCH (a:Entity {user_id: $uid})-[r]->(b:Entity {user_id: $uid}) "
            "WHERE a.removed_at IS NULL AND b.removed_at IS NULL "
            "RETURN a.name AS src, coalesce(r.kind, type(r)) AS rel, b.name AS dst",
            uid=str(user_id),
        )
        async for record in result:
            edges.append({"src": record["src"], "rel": record["rel"], "dst": record["dst"]})
    return {"nodes": nodes, "edges": edges}
