import uuid

from app.services.neo4j.get_driver import get_driver
from app.services.neo4j.models import KGEntity, KGRelation
from app.services.neo4j.open_session import open_session


async def upsert_kg(
    user_id: uuid.UUID,
    entities: list[KGEntity],
    relations: list[KGRelation],
) -> None:
    driver = get_driver()
    async with open_session(driver) as session:
        for ent in entities:
            await session.run(
                """
                MERGE (u:User {id: $uid})
                MERGE (n:Entity {user_id: $uid, name: $name})
                SET n.type = $type, n += $props
                MERGE (u)-[:KNOWS]->(n)
                """,
                uid=str(user_id),
                name=ent.name,
                type=ent.type,
                props=ent.props,
            )
        for rel in relations:
            # Stable relation type :RELATED — the LLM-supplied label (e.g. FRIENDS_WITH, WORKS_AT) lives as a `kind` property on the edge.
            # Keeps the Cypher fully literal (no string interpolation, no LiteralString casts) and still lets readers filter by kind.
            kind = "".join(c if c.isalnum() else "_" for c in rel.relation.upper()) or "RELATED"
            await session.run(
                """
                MATCH (a:Entity {user_id: $uid, name: $src})
                MATCH (b:Entity {user_id: $uid, name: $dst})
                MERGE (a)-[r:RELATED]->(b)
                SET r.kind = $kind
                """,
                uid=str(user_id),
                src=rel.src_name,
                dst=rel.dst_name,
                kind=kind,
            )
