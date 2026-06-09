"""Tests for POST /conversation/{session_id}/transcript."""

import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_session(db: DBConn, user_id: uuid.UUID) -> uuid.UUID:
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user_id,
    )
    return session_id


async def test_append_transcript_writes_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    now = datetime.now(UTC)
    resp = await client.post(
        f"/conversation/{session_id}/transcript",
        json={
            "speaker": "user",
            "text": "hello there",
            "started_at": now.isoformat(),
            "ended_at": now.isoformat(),
        },
    )
    assert resp.status_code == 204
    row = await db.fetchrow(
        "SELECT speaker, text FROM transcripts WHERE session_id = $1", session_id
    )
    assert row is not None
    assert row["speaker"] == "user"
    assert row["text"] == "hello there"


async def test_append_transcript_404_for_unknown_session(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    now = datetime.now(UTC)
    resp = await client.post(
        f"/conversation/{uuid.uuid4()}/transcript",
        json={
            "speaker": "user",
            "text": "x",
            "started_at": now.isoformat(),
            "ended_at": now.isoformat(),
        },
    )
    assert resp.status_code == 404


async def test_append_transcript_rejects_invalid_speaker(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    now = datetime.now(UTC)
    resp = await client.post(
        f"/conversation/{session_id}/transcript",
        json={
            "speaker": "alien",
            "text": "x",
            "started_at": now.isoformat(),
            "ended_at": now.isoformat(),
        },
    )
    assert resp.status_code == 422
