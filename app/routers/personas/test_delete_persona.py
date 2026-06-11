"""Tests for the delete-persona endpoint (DELETE /personas/{id}).

Covers the happy-path row removal plus the two guards: presets are read-only (403) and another user's persona is not found (404), never deletable."""

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
    is_public: bool = False,
    voice_id: str = "NATM1",
) -> uuid.UUID:
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, $2, '', $3, NULL, NULL, NULL, NULL, NULL, NULL, $4, $5)""",
        persona_id,
        name,
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


async def test_delete_persona_removes_owned_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"])
    resp = await client.delete(f"/personas/{persona_id}")
    assert resp.status_code == 204
    row = await db.fetchrow("SELECT id FROM personas WHERE id = $1", persona_id)
    assert row is None


async def test_delete_persona_rejects_preset(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.delete(f"/personas/{PRESETS[0].id}")
    assert resp.status_code == 403


async def test_delete_persona_other_users_is_404_and_leaves_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = await _seed_other_user(db)
    persona_id = await _seed_persona(db, other_id, name="Theirs", is_public=True)
    resp = await client.delete(f"/personas/{persona_id}")
    assert resp.status_code == 404
    # The guard must not have removed the other user's row.
    row = await db.fetchrow("SELECT id FROM personas WHERE id = $1", persona_id)
    assert row is not None


async def test_delete_persona_unknown_id_is_404(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.delete(f"/personas/{uuid.uuid4()}")
    assert resp.status_code == 404
