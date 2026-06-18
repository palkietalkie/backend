"""Tests for GET /conversation/sessions."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.personas.presets.preset_list import PRESETS
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_list_sessions_empty(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/conversation/sessions")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_sessions_orders_by_started_at_desc_and_respects_limit(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    ids: list[uuid.UUID] = []
    for offset in (0, 5, 10):
        sid = uuid.uuid4()
        await db.execute(
            "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, $3)",
            sid,
            user["id"],
            now - timedelta(minutes=offset),
        )
        ids.append(sid)

    resp = await client.get("/conversation/sessions", params={"limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    # Most recent first.
    assert uuid.UUID(body[0]["session_id"]) == ids[0]
    assert uuid.UUID(body[1]["session_id"]) == ids[1]


async def test_list_sessions_only_returns_own_sessions(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    other_user = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other_user,
        f"u_other_{other_user.hex[:8]}",
    )
    foreign = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        foreign,
        other_user,
    )
    mine = uuid.uuid4()
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, started_at) VALUES ($1, $2, NOW())",
        mine,
        user["id"],
    )

    resp = await client.get("/conversation/sessions")
    ids = [uuid.UUID(row["session_id"]) for row in resp.json()]
    assert mine in ids
    assert foreign not in ids


async def test_list_sessions_resolves_preset_persona_name(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # History shows persona_name, not the raw persona UUID; a preset id must resolve to its name.
    client, user = app_with_overrides
    preset = PRESETS[0]
    await db.execute(
        "INSERT INTO conversation_sessions (id, user_id, persona_id, started_at) VALUES ($1, $2, $3, NOW())",
        uuid.uuid4(),
        user["id"],
        preset.id,
    )
    body = (await client.get("/conversation/sessions")).json()
    assert body[0]["persona_name"] == preset.name
