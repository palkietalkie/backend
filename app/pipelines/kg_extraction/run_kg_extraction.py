import uuid

from app.pipelines.kg_extraction.extract_kg import extract_kg
from app.services.neo4j.upsert_kg import upsert_kg
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_session_user_turns import fetch_session_user_turns


async def run_kg_extraction(
    session_id: uuid.UUID, user_id: uuid.UUID, db: DBConn
) -> int:
    # Returns total node + edge count written to the KG.
    texts = await fetch_session_user_turns(session_id, db)
    entities, relations = await extract_kg(texts)
    if not entities and not relations:
        return 0
    await upsert_kg(user_id, entities, relations)
    return len(entities) + len(relations)
