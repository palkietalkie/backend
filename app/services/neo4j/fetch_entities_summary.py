import uuid

from app.services.neo4j.get_driver import get_driver


async def fetch_entities_summary(user_id: uuid.UUID, limit: int = 20) -> list[str]:
    driver = get_driver()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n:Entity {user_id: $uid}) RETURN n.name AS name, n.type AS type LIMIT $lim",
            uid=str(user_id),
            lim=limit,
        )
        return [f"{r['name']} ({r['type']})" async for r in result]
