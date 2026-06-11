import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_recall_transcripts_returns_matches(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
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
        "I love bouldering on weekends",
        now,
    )
    resp = await client.get("/recall/transcripts", params={"q": "bouldering"})
    assert resp.status_code == 200
    turns = resp.json()["turns"]
    assert any("bouldering" in t["text"] for t in turns)


async def test_recall_facts_is_best_effort_when_kg_unavailable(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    # No Neo4j reachable in the test env — the tool endpoint must degrade to empty, not 500, so a mid-conversation tool call never breaks the session.
    client, _ = app_with_overrides
    resp = await client.get("/recall/facts", params={"q": "naoto"})
    assert resp.status_code == 200
    assert resp.json() == {"entities": []}
