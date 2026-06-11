"""Tests for the unlike-persona endpoint (DELETE /personas/{id}/like).

Covers removing an existing like (count decrement, never below zero), the no-op path when the user never liked, and that a preset unlike removes the like row without touching any personas row."""

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


async def test_unlike_removes_like_and_drops_count(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    await client.post(f"/personas/{persona_id}/like")
    resp = await client.delete(f"/personas/{persona_id}/like")
    assert resp.status_code == 204

    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 0
    like_row = await db.fetchrow(
        "SELECT id FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        persona_id,
    )
    assert like_row is None


async def test_unlike_when_not_liked_is_noop(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    resp = await client.delete(f"/personas/{persona_id}/like")
    assert resp.status_code == 204
    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 0


async def test_unlike_count_never_goes_negative(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    await client.post(f"/personas/{persona_id}/like")
    await client.delete(f"/personas/{persona_id}/like")
    # Second unlike has no like row to delete; count must stay clamped at 0.
    resp = await client.delete(f"/personas/{persona_id}/like")
    assert resp.status_code == 204
    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 0


async def test_unlike_preset_removes_like_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    preset_id = PRESETS[0].id
    await client.post(f"/personas/{preset_id}/like")
    resp = await client.delete(f"/personas/{preset_id}/like")
    assert resp.status_code == 204
    like_row = await db.fetchrow(
        "SELECT id FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        preset_id,
    )
    assert like_row is None
