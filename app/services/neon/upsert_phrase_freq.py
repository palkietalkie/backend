import uuid
from datetime import UTC, datetime

from app.services.neon.db_conn import DBConn


async def upsert_phrase_freq(
    user_id: uuid.UUID,
    phrases: list[tuple[str, int]],
    db: DBConn,
) -> int:
    if not phrases:
        return 0
    now = datetime.now(UTC)
    for phrase, count in phrases:
        await db.execute(
            """INSERT INTO phrase_freq (user_id, phrase, count, last_used_at)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id, phrase) DO UPDATE SET
                   count        = phrase_freq.count + EXCLUDED.count,
                   last_used_at = EXCLUDED.last_used_at""",
            user_id,
            phrase[:255],
            count,
            now,
        )
    return len(phrases)
