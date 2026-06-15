import uuid

from app.services.neo4j.get_neo4j_driver import get_neo4j_driver
from app.services.neo4j.is_self_reference import is_self_reference
from app.services.neo4j.models import KGEntity, KGRelation
from app.services.neo4j.open_session import open_session


async def upsert_kg(
    user_id: uuid.UUID,
    entities: list[KGEntity],
    relations: list[KGRelation],
    user_name: str | None = None,
) -> None:
    driver = get_neo4j_driver()
    async with open_session(driver) as session:
        for ent in entities:
            if is_self_reference(ent.name, user_name=user_name):
                # The speaker is the User node, not an Entity — fold any self-attributes onto it.
                await session.run(
                    "MERGE (u:User {id: $uid}) SET u += $props",
                    uid=str(user_id),
                    props=ent.props,
                )
                continue
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
            src_self = is_self_reference(rel.src_name, user_name=user_name)
            dst_self = is_self_reference(rel.dst_name, user_name=user_name)
            if src_self and dst_self:
                continue  # a self→self edge carries no information
            if src_self:
                # User → Entity: the speaker's relationship to a thing (likes, owns, plays, knows).
                await session.run(
                    """
                    MERGE (u:User {id: $uid})
                    MATCH (b:Entity {user_id: $uid, name: $dst})
                    MERGE (u)-[r:RELATED]->(b)
                    SET r.kind = $kind
                    """,
                    uid=str(user_id),
                    dst=rel.dst_name,
                    kind=kind,
                )
            elif dst_self:
                await session.run(
                    """
                    MERGE (u:User {id: $uid})
                    MATCH (a:Entity {user_id: $uid, name: $src})
                    MERGE (a)-[r:RELATED]->(u)
                    SET r.kind = $kind
                    """,
                    uid=str(user_id),
                    src=rel.src_name,
                    kind=kind,
                )
            else:
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
