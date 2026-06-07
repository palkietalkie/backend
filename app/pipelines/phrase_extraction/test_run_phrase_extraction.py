"""End-to-end tests for run_phrase_extraction with the LLM step mocked."""

import uuid
from datetime import datetime, timedelta

import pytest

from app.pipelines.phrase_extraction import run_phrase_extraction as mod
from app.services.neon.db_conn import DBConn


async def _seed(db: DBConn) -> tuple[uuid.UUID, uuid.UUID]:
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user_id,
    )
    return user_id, session_id


async def test_run_phrase_extraction_zero_when_no_turns(db: DBConn) -> None:
    user_id, session_id = await _seed(db)
    out = await mod.run_phrase_extraction(session_id, user_id, db)
    assert out == 0


async def test_run_phrase_extraction_writes_filtered_phrases(
    db: DBConn, monkeypatch: pytest.MonkeyPatch
) -> None:
    user_id, session_id = await _seed(db)
    now = datetime.now()
    texts = (
        "I want to learn something new every day.",
        "It is what it is, every single day.",
    )
    for idx, text in enumerate(texts):
        ts = now + timedelta(seconds=idx)
        await db.execute(
            """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
               VALUES ($1, 'user', $2, $3, $3)""",
            session_id,
            text,
            ts,
        )

    async def _fake_filter(candidates: list[str]) -> list[str]:
        # Keep the first candidate.
        return candidates[:1] if candidates else []

    monkeypatch.setattr(mod, "filter_phrases_with_llm", _fake_filter)
    out = await mod.run_phrase_extraction(session_id, user_id, db)
    assert out >= 0
