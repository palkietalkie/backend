"""Tests for the session_audio TTL pruner."""

import uuid
from datetime import UTC, datetime, timedelta

from app.pipelines.session_audio.prune_expired_audio import prune_expired_audio_once
from app.services.neon.db_conn import DBConn


async def _seed(
    db: DBConn,
    *,
    expires_at: datetime,
    audio: bytes = b"x",
) -> uuid.UUID:
    user_id = uuid.uuid4()
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        session_id,
        user_id,
    )
    await db.execute(
        """INSERT INTO session_audio
                (session_id, source, user_id, audio, bytes, format, expires_at)
           VALUES ($1, 'mic', $2, $3, $4, 'audio/wav+deflate', $5)""",
        session_id,
        user_id,
        audio,
        len(audio),
        expires_at,
    )
    return session_id


async def test_prune_deletes_only_expired_rows(db: DBConn) -> None:
    now = datetime.now(UTC)
    expired = await _seed(db, expires_at=now - timedelta(hours=1))
    fresh = await _seed(db, expires_at=now + timedelta(days=10))

    deleted = await prune_expired_audio_once(db)

    assert deleted >= 1
    remaining_ids = {
        row["session_id"]
        for row in await db.fetch(
            "SELECT session_id FROM session_audio WHERE session_id = ANY($1)", [expired, fresh]
        )
    }
    assert expired not in remaining_ids
    assert fresh in remaining_ids


async def test_prune_returns_zero_when_nothing_expired(db: DBConn) -> None:
    now = datetime.now(UTC)
    fresh = await _seed(db, expires_at=now + timedelta(days=1))

    deleted = await prune_expired_audio_once(db)
    assert deleted == 0

    row = await db.fetchrow("SELECT 1 FROM session_audio WHERE session_id = $1", fresh)
    assert row is not None
