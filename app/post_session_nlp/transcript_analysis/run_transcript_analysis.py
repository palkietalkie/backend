import uuid

from app.post_session_nlp.transcript_analysis.count_lemmas import count_lemmas
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_session_user_turns import fetch_session_user_turns
from app.services.neon.upsert_word_freq import upsert_word_freq


async def run_transcript_analysis(session_id: uuid.UUID, user_id: uuid.UUID, db: DBConn) -> int:
    texts = await fetch_session_user_turns(session_id, db)
    if not texts:
        return 0
    counts = count_lemmas(texts)
    return await upsert_word_freq(user_id, counts, db)
