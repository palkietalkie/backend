import uuid

from app.post_session_nlp.phrase_extraction.filter_phrases_with_llm import (
    filter_phrases_with_llm,
)
from app.post_session_nlp.phrase_extraction.find_candidate_phrases import (
    find_candidate_phrases,
)
from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_session_user_turns import fetch_session_user_turns
from app.services.neon.upsert_phrase_freq import upsert_phrase_freq


async def run_phrase_extraction(session_id: uuid.UUID, user_id: uuid.UUID, db: DBConn) -> int:
    texts = await fetch_session_user_turns(session_id, db)
    if not texts:
        return 0
    candidates = find_candidate_phrases(texts)
    if not candidates:
        return 0
    candidate_map = dict(candidates)
    kept = await filter_phrases_with_llm(list(candidate_map.keys()))
    rows = [(phrase, candidate_map.get(phrase, 1)) for phrase in kept]
    return await upsert_phrase_freq(user_id, rows, db)
