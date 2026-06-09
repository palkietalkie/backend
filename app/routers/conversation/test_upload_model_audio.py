"""Contract tests for POST /conversation/{session_id}/audio/model — companion to /audio/mic."""

import uuid

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

ROUTE = "/conversation/{sid}/audio/model"
CT = "audio/wav+deflate"


async def _seed_session(db: DBConn, user_id: uuid.UUID) -> uuid.UUID:
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user_id,
    )
    return session_id


async def test_upload_model_audio_stores_row_with_model_source(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    payload = b"MODELWAVDATA" * 100

    resp = await client.post(
        ROUTE.format(sid=session_id), content=payload, headers={"Content-Type": CT}
    )
    assert resp.status_code == 204
    row = await db.fetchrow(
        "SELECT bytes, format, source, expires_at - created_at AS ttl FROM session_audio WHERE session_id = $1 AND source = 'model'",
        session_id,
    )
    assert row is not None
    assert row["source"] == "model"
    assert row["bytes"] == len(payload)
    assert row["format"] == CT
    assert 13 < row["ttl"].days <= 14


async def test_upload_model_audio_does_not_clobber_mic_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # Mic and model land on the same (session_id, source) PK in `session_audio`; one must NOT overwrite the other.
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    await client.post(
        f"/conversation/{session_id}/audio/mic",
        content=b"MIC" * 100,
        headers={"Content-Type": CT},
    )
    await client.post(
        ROUTE.format(sid=session_id),
        content=b"MODEL" * 100,
        headers={"Content-Type": CT},
    )
    rows = await db.fetch(
        "SELECT source FROM session_audio WHERE session_id = $1 ORDER BY source",
        session_id,
    )
    assert [r["source"] for r in rows] == ["mic", "model"]


async def test_upload_model_audio_rejects_foreign_session(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _user = app_with_overrides
    other = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other,
        f"u_{other.hex[:8]}",
    )
    session_id = await _seed_session(db, other)
    resp = await client.post(
        ROUTE.format(sid=session_id), content=b"x", headers={"Content-Type": CT}
    )
    assert resp.status_code == 404


async def test_upload_model_audio_rejects_empty_body(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    resp = await client.post(
        ROUTE.format(sid=session_id), content=b"", headers={"Content-Type": CT}
    )
    assert resp.status_code == 400


async def test_upload_model_audio_upserts_on_retry(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])
    await client.post(
        ROUTE.format(sid=session_id), content=b"v1" * 100, headers={"Content-Type": CT}
    )
    await client.post(
        ROUTE.format(sid=session_id), content=b"v2" * 200, headers={"Content-Type": CT}
    )
    row = await db.fetchrow(
        "SELECT bytes FROM session_audio WHERE session_id = $1 AND source = 'model'",
        session_id,
    )
    assert row is not None
    assert row["bytes"] == 400
