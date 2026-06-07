"""Contract tests for POST /conversation/{session_id}/audio/mic."""

import uuid

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

ROUTE = "/conversation/{sid}/audio/mic"
CT = "audio/wav+deflate"


async def _seed_session(db: DBConn, user_id: uuid.UUID) -> uuid.UUID:
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user_id,
    )
    return session_id


async def test_upload_mic_audio_stores_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    payload = b"FAKEWAVDATA" * 200

    resp = await client.post(
        ROUTE.format(sid=session_id), content=payload, headers={"Content-Type": CT}
    )
    assert resp.status_code == 204

    row = await db.fetchrow(
        "SELECT bytes, format, expires_at - created_at AS ttl FROM session_audio WHERE session_id = $1 AND source = 'mic'",
        session_id,
    )
    assert row is not None
    assert row["bytes"] == len(payload)
    assert row["format"] == CT
    assert 13 < row["ttl"].days <= 14


async def test_upload_mic_audio_rejects_foreign_session(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _user = app_with_overrides
    other_user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other_user_id,
        f"user_other_{other_user_id.hex[:8]}",
    )
    session_id = await _seed_session(db, other_user_id)
    resp = await client.post(
        ROUTE.format(sid=session_id), content=b"x", headers={"Content-Type": CT}
    )
    assert resp.status_code == 404


async def test_upload_mic_audio_rejects_empty_body(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    resp = await client.post(
        ROUTE.format(sid=session_id), content=b"", headers={"Content-Type": CT}
    )
    assert resp.status_code == 400


async def test_upload_mic_audio_upserts_on_retry(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    first = await client.post(
        ROUTE.format(sid=session_id), content=b"v1" * 100, headers={"Content-Type": CT}
    )
    assert first.status_code == 204
    second = await client.post(
        ROUTE.format(sid=session_id), content=b"v2" * 200, headers={"Content-Type": CT}
    )
    assert second.status_code == 204
    row = await db.fetchrow(
        "SELECT bytes FROM session_audio WHERE session_id = $1 AND source = 'mic'",
        session_id,
    )
    assert row is not None
    assert row["bytes"] == 400
