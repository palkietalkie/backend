import uuid
from datetime import UTC, datetime

from app.services.neon.db_conn import DBConn


async def upsert_word_freq(
    user_id: uuid.UUID,
    counts: dict[str, int],
    db: DBConn,
) -> int:
    # Increment running per-(user, lemma) count. Returns the number of distinct lemmas upserted.
    if not counts:
        return 0
    now = datetime.now(UTC)
    for lemma, count in counts.items():
        await db.execute(
            """INSERT INTO word_freq (user_id, lemma, count, last_used_at)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id, lemma) DO UPDATE SET
                   count        = word_freq.count + EXCLUDED.count,
                   last_used_at = EXCLUDED.last_used_at""",
            user_id,
            lemma[:64],
            count,
            now,
        )
    return len(counts)
