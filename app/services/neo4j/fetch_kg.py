import uuid
from typing import Any

from app.services.neo4j.get_driver import get_driver


async def fetch_kg(user_id: uuid.UUID) -> dict[str, Any]:
    driver = get_driver()
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n:Entity {user_id: $uid}) RETURN n.name AS name, n.type AS type, "
            "properties(n) AS props",
            uid=str(user_id),
        )
        async for record in result:
            nodes.append(
                {
                    "name": record["name"],
                    "type": record["type"],
                    "props": dict(record["props"] or {}),
                }
            )

        # The edge type is always :RELATED; the LLM-supplied label lives in `r.kind`.
        # Older rows (from before the schema change) may not have a kind property — coalesce to the edge type so the response is never null.
        result = await session.run(
            "MATCH (a:Entity {user_id: $uid})-[r]->(b:Entity {user_id: $uid}) "
            "RETURN a.name AS src, coalesce(r.kind, type(r)) AS rel, b.name AS dst",
            uid=str(user_id),
        )
        async for record in result:
            edges.append({"src": record["src"], "rel": record["rel"], "dst": record["dst"]})
    return {"nodes": nodes, "edges": edges}
