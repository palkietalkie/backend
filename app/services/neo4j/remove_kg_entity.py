import uuid

from app.services.neo4j.get_neo4j_driver import get_neo4j_driver
from app.services.neo4j.open_session import open_session


async def remove_kg_entity(user_id: uuid.UUID, name: str) -> None:
    """Soft-delete a KG entity the user judged wrong (swipe-to-remove on the KG screen).

    Sets `removed_at` so fetch_kg hides the node and its edges. The node + its props stay (recoverable), and crucially the pipeline's `upsert_kg` MERGEs on (user_id, name) and only SETs type/props, it never clears `removed_at`, so a later re-mention of the same name can't resurrect it. The removal is sticky, which is the point: the user said it's wrong.
    """
    driver = get_neo4j_driver()
    async with open_session(driver) as session:
        await session.run(
            "MATCH (n:Entity {user_id: $uid, name: $name}) SET n.removed_at = timestamp()",
            uid=str(user_id),
            name=name,
        )
