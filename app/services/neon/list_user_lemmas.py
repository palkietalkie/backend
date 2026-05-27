import uuid

from app.services.neon.db_conn import DBConn


async def list_user_lemmas(db: DBConn, user_id: uuid.UUID) -> set[str]:
    rows = await db.fetch(
        "SELECT lemma FROM word_freq WHERE user_id = $1",
        user_id,
    )
    return {row["lemma"] for row in rows}
