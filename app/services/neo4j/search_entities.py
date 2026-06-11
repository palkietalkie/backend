import uuid
from typing import Any

from app.services.neo4j.get_neo4j_driver import get_neo4j_driver
from app.services.neo4j.open_session import open_session


def _scalar(value: object) -> str:
    return "" if value is None else str(value)


async def search_entities(user_id: uuid.UUID, query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Find KG entities whose name matches `query` (case-insensitive substring) plus their outgoing relations. Backs the conversation-time facts-recall tool — the model calls this when it needs a structured fact about a person/place/project the user mentioned before ("who is Naoto, again?")."""
    driver = get_neo4j_driver()
    out: list[dict[str, Any]] = []
    async with open_session(driver) as session:
        # Return relations as two parallel scalar lists (rel kinds + target names) rather than a list of maps: the neo4j driver types record fields as Any, and parallel string lists can be zipped without any member access on an unknown-typed value (so no cast/ignore needed). The CASE + WHERE filters out the null row OPTIONAL MATCH emits for entities with no edge, keeping the two lists aligned.
        result = await session.run(
            """MATCH (n:Entity {user_id: $uid})
               WHERE toLower(n.name) CONTAINS toLower($q)
               OPTIONAL MATCH (n)-[r:RELATED]->(m:Entity {user_id: $uid})
               RETURN n.name AS name, n.type AS type,
                      [x IN collect(CASE WHEN m IS NOT NULL THEN coalesce(r.kind, 'related') END)
                         WHERE x IS NOT NULL] AS rels,
                      [x IN collect(m.name) WHERE x IS NOT NULL] AS targets
               LIMIT $limit""",
            uid=str(user_id),
            q=query,
            limit=limit,
        )
        async for rec in result:
            relations = [
                {"rel": _scalar(rel), "target": _scalar(tgt)}
                for rel, tgt in zip(rec["rels"], rec["targets"], strict=True)
            ]
            out.append(
                {"name": _scalar(rec["name"]), "type": _scalar(rec["type"]), "relations": relations}
            )
    return out
