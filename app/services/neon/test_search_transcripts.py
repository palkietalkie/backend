import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow
from app.services.neon.search_transcripts import search_transcripts


async def test_search_transcripts_full_text_matches_and_scopes_to_user(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    _, user = app_with_overrides
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user["id"],
    )
    now = datetime.now(UTC)
    await db.execute(
        "INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at) "
        "VALUES ($1, 'user', $2, $3, $3)",
        session_id,
        "I went bouldering at the climbing gym on Saturday",
        now,
    )
    await db.execute(
        "INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at) "
        "VALUES ($1, 'persona', $2, $3, $3)",
        session_id,
        "How did the pasta recipe turn out",
        now,
    )

    hits = await search_transcripts(user["id"], "climbing", db)
    assert any("bouldering" in h["text"] for h in hits)
    assert all("pasta" not in h["text"] for h in hits), "FTS must not match unrelated turns"
