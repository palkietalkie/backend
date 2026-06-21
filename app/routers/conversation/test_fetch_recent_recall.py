import uuid
from datetime import UTC, datetime, timedelta

from app.routers.conversation.fetch_recent_recall import fetch_recent_recall
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _finished_session(
    db: DBConn,
    user_id: uuid.UUID,
    persona_id: uuid.UUID,
    target_language: str | None,
    text: str,
    ended_at: datetime,
) -> None:
    session_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, persona_id, started_at, ended_at, target_language)
           VALUES ($1, $2, $3, $4, $5, $6)""",
        session_id,
        user_id,
        persona_id,
        ended_at - timedelta(minutes=5),
        ended_at,
        target_language,
    )
    await db.execute(
        "INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at) "
        "VALUES ($1, 'persona', $2, $3, $3)",
        session_id,
        text,
        ended_at,
    )


async def test_recall_excludes_other_language_sessions(db: DBConn, fake_user: UserRow) -> None:
    # The reported bug: a Japanese session's transcript leaked into an English session's recall and the tutor kept speaking Japanese. Recall must only surface same-language history.
    persona_id = uuid.uuid4()
    now = datetime.now(UTC)
    await _finished_session(
        db,
        fake_user["id"],
        persona_id,
        "Japanese",
        "確かにそうやな、コートの風が涼しい。",
        now - timedelta(hours=1),
    )
    await _finished_session(
        db, fake_user["id"], persona_id, "English", "Right, the wind off the court felt cool.", now
    )
    recall = await fetch_recent_recall(fake_user["id"], persona_id, "English", db)
    assert recall is not None
    assert "wind off the court" in recall
    assert "コートの風" not in recall


async def test_recall_excludes_untagged_legacy_sessions(db: DBConn, fake_user: UserRow) -> None:
    # Pre-fix rows have NULL target_language. We exclude them rather than guess — a missed callback beats a wrong-language opening.
    persona_id = uuid.uuid4()
    await _finished_session(
        db, fake_user["id"], persona_id, None, "legacy untagged turn", datetime.now(UTC)
    )
    assert await fetch_recent_recall(fake_user["id"], persona_id, "English", db) is None


async def test_recall_is_per_persona(db: DBConn, fake_user: UserRow) -> None:
    other_persona = uuid.uuid4()
    target_persona = uuid.uuid4()
    await _finished_session(
        db, fake_user["id"], other_persona, "English", "another persona's turn", datetime.now(UTC)
    )
    assert await fetch_recent_recall(fake_user["id"], target_persona, "English", db) is None


async def test_recall_returns_matching_language(db: DBConn, fake_user: UserRow) -> None:
    persona_id = uuid.uuid4()
    await _finished_session(
        db,
        fake_user["id"],
        persona_id,
        "English",
        "you mentioned the demo last time",
        datetime.now(UTC),
    )
    recall = await fetch_recent_recall(fake_user["id"], persona_id, "English", db)
    assert recall is not None
    assert "demo last time" in recall
