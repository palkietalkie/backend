"""Tests for POST /conversation/{session_id}/end."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from app.routers.conversation import end_conversation as end_conversation_mod
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_session(
    db: DBConn, user_id: uuid.UUID, started_at: datetime | None = None
) -> uuid.UUID:
    session_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, $3)",
        session_id,
        user_id,
        started_at or datetime.now(UTC),
    )
    return session_id


async def test_end_conversation_writes_duration_and_emits_event(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Skip running background pipelines (they would acquire their own pool conn).
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, user = app_with_overrides
    started = datetime.now(UTC) - timedelta(seconds=120)
    session_id = await _seed_session(db, user["id"], started)

    resp = await client.post(f"/conversation/{session_id}/end")
    assert resp.status_code == 200
    body = resp.json()
    assert uuid.UUID(body["session_id"]) == session_id
    assert body["duration_seconds"] >= 119

    row = await db.fetchrow(
        "SELECT ended_at, duration_seconds FROM conversation_sessions WHERE id = $1",
        session_id,
    )
    assert row is not None
    assert row["ended_at"] is not None
    assert row["duration_seconds"] >= 119

    events = await db.fetch(
        "SELECT event_type FROM events WHERE user_id = $1 AND event_type = 'conversation_end'",
        user["id"],
    )
    assert len(events) == 1


async def test_end_conversation_returns_404_for_unknown_session(
    app_with_overrides: tuple[AsyncClient, UserRow],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, _ = app_with_overrides
    resp = await client.post(f"/conversation/{uuid.uuid4()}/end")
    assert resp.status_code == 404


async def test_end_conversation_rejects_foreign_session(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    session_id = await _seed_session(db, other_id)
    resp = await client.post(f"/conversation/{session_id}/end")
    assert resp.status_code == 404


async def test_end_conversation_stores_reported_tokens(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])

    resp = await client.post(
        f"/conversation/{session_id}/end", json={"input_tokens": 12000, "output_tokens": 8000}
    )
    assert resp.status_code == 200
    row = await db.fetchrow(
        "SELECT input_tokens, output_tokens FROM conversation_sessions WHERE id = $1", session_id
    )
    assert row is not None
    assert row["input_tokens"] == 12000
    assert row["output_tokens"] == 8000


async def test_end_conversation_without_tokens_leaves_them_null(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Backward compatibility: the build already in TestFlight POSTs an empty body. It must still end, with token columns left NULL (not a wrong 0).
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, user = app_with_overrides
    session_id = await _seed_session(db, user["id"])

    resp = await client.post(f"/conversation/{session_id}/end")
    assert resp.status_code == 200
    row = await db.fetchrow(
        "SELECT input_tokens, output_tokens FROM conversation_sessions WHERE id = $1", session_id
    )
    assert row is not None
    assert row["input_tokens"] is None
    assert row["output_tokens"] is None


async def test_end_conversation_clamps_negative_duration_to_zero(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _noop(*_args: object, **_kwargs: object) -> None:
        return None

    monkeypatch.setattr(end_conversation_mod, "run_post_session_pipelines", _noop)
    client, user = app_with_overrides
    # started_at in the future would yield a negative duration; route clamps to 0.
    started = datetime.now(UTC) + timedelta(seconds=60)
    session_id = await _seed_session(db, user["id"], started)

    resp = await client.post(f"/conversation/{session_id}/end")
    assert resp.status_code == 200
    assert resp.json()["duration_seconds"] == 0
