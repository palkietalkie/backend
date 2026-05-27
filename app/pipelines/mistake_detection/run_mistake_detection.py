import uuid

from app.pipelines.mistake_detection.extract_mistakes import extract_mistakes
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_session_user_turns import fetch_session_user_turns
from app.services.neon.upsert_mistakes import upsert_mistakes


async def run_mistake_detection(
    session_id: uuid.UUID, user_id: uuid.UUID, db: DBConn
) -> int:
    texts = await fetch_session_user_turns(session_id, db)
    mistakes = await extract_mistakes(texts)
    return await upsert_mistakes(user_id, mistakes, db)
