import uuid

from app.services.neo4j.get_driver import get_driver
from app.services.neo4j.models import KGEntity, KGRelation


async def upsert_kg(
    user_id: uuid.UUID,
    entities: list[KGEntity],
    relations: list[KGRelation],
) -> None:
    driver = get_driver()
    async with driver.session() as session:
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
            # Relationship type is dynamic; sanitize to ASCII upper underscore.
            rel_type = "".join(c if c.isalnum() else "_" for c in rel.relation.upper()) or "RELATED"
            await session.run(
                f"""
                MATCH (a:Entity {{user_id: $uid, name: $src}})
                MATCH (b:Entity {{user_id: $uid, name: $dst}})
                MERGE (a)-[:{rel_type}]->(b)
                """,  # type: ignore[arg-type]
                uid=str(user_id),
                src=rel.src_name,
                dst=rel.dst_name,
            )
