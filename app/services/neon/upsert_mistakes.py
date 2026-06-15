import uuid
from datetime import UTC, datetime

from app.post_session_nlp.mistake_detection.mistake_record import MistakeRecord
from app.services.neon.db_conn import DBConn


async def upsert_mistakes(
    user_id: uuid.UUID,
    mistakes: list[MistakeRecord],
    db: DBConn,
) -> int:
    if not mistakes:
        return 0
    now = datetime.now(UTC)
    for m in mistakes:
        await db.execute(
            """INSERT INTO mistakes (id, user_id, original, corrected, category, count, last_seen_at)
               VALUES ($1, $2, $3, $4, $5, 1, $6)
               ON CONFLICT ON CONSTRAINT uq_mistake_user_text DO UPDATE SET
                   count        = mistakes.count + 1,
                   last_seen_at = EXCLUDED.last_seen_at""",
            uuid.uuid4(),
            user_id,
            m.original,
            m.corrected,
            m.category,
            now,
        )
    return len(mistakes)
