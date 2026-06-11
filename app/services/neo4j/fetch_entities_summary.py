import uuid

from app.services.neo4j.get_neo4j_driver import get_neo4j_driver
from app.services.neo4j.open_session import open_session


async def fetch_entities_summary(user_id: uuid.UUID, limit: int = 20) -> list[str]:
    driver = get_neo4j_driver()
    async with open_session(driver) as session:
        result = await session.run(
            "MATCH (n:Entity {user_id: $uid}) RETURN n.name AS name, n.type AS type LIMIT $lim",
            uid=str(user_id),
            lim=limit,
        )
        return [f"{r['name']} ({r['type']})" async for r in result]
