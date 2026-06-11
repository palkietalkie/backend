"""Tests for the update-persona endpoint (PATCH /personas/{id}).

Covers partial field writes, the empty-body no-op, voice-id validation, and the guards: presets are read-only (403) and another user's persona is not found (404)."""

import uuid

from httpx import AsyncClient

from app.personas.presets.preset_list import PRESETS
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_persona(
    db: DBConn,
    user_id: uuid.UUID,
    *,
    name: str = "Custom Tutor",
    description: str = "",
    is_public: bool = False,
    voice_id: str = "NATM1",
) -> uuid.UUID:
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, $2, $3, $4, NULL, NULL, NULL, NULL, NULL, NULL, $5, $6)""",
        persona_id,
        name,
        description,
        voice_id,
        is_public,
        user_id,
    )
    return persona_id


async def _seed_other_user(db: DBConn) -> uuid.UUID:
    other_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    return other_id


async def test_update_writes_only_provided_fields(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="Original", description="keep me")
    resp = await client.patch(f"/personas/{persona_id}", json={"name": "Renamed"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Renamed"
    # description was not in the patch body, so it must be untouched.
    assert body["description"] == "keep me"

    row = await db.fetchrow("SELECT name, description FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["name"] == "Renamed"
    assert row["description"] == "keep me"


async def test_update_can_flip_is_public(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=False)
    resp = await client.patch(f"/personas/{persona_id}", json={"is_public": True})
    assert resp.status_code == 200
    assert resp.json()["is_public"] is True
    row = await db.fetchrow("SELECT is_public FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["is_public"] is True


async def test_update_empty_body_is_noop(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="StayPut")
    resp = await client.patch(f"/personas/{persona_id}", json={})
    assert resp.status_code == 200
    assert resp.json()["name"] == "StayPut"
    row = await db.fetchrow("SELECT name FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["name"] == "StayPut"


async def test_update_rejects_unknown_voice(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="Keep")
    resp = await client.patch(f"/personas/{persona_id}", json={"voice_id": "BOGUS"})
    assert resp.status_code == 400
    # Rejected before any write — name stays.
    row = await db.fetchrow("SELECT name FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["name"] == "Keep"


async def test_update_rejects_preset(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.patch(f"/personas/{PRESETS[0].id}", json={"name": "Hijack"})
    assert resp.status_code == 403


async def test_update_other_users_is_404_and_unchanged(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = await _seed_other_user(db)
    persona_id = await _seed_persona(db, other_id, name="Theirs", is_public=True)
    resp = await client.patch(f"/personas/{persona_id}", json={"name": "Hijack"})
    assert resp.status_code == 404
    row = await db.fetchrow("SELECT name FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["name"] == "Theirs"
