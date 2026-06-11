"""Tests for the like-persona endpoint (POST /personas/{id}/like).

Covers the denormalized like_count bump, idempotency on the unique like constraint, preset likes (recorded in persona_likes without a DB persona row), and the 404 visibility guards for unknown / other-users' private personas."""

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


async def test_like_persona_bumps_count_and_records_like(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    other_id = await _seed_other_user(db)
    persona_id = await _seed_persona(db, other_id, name="Public", is_public=True)
    resp = await client.post(f"/personas/{persona_id}/like")
    assert resp.status_code == 204

    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 1

    like_row = await db.fetchrow(
        "SELECT id FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        persona_id,
    )
    assert like_row is not None


async def test_like_persona_is_idempotent(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    first = await client.post(f"/personas/{persona_id}/like")
    second = await client.post(f"/personas/{persona_id}/like")
    assert first.status_code == 204
    assert second.status_code == 204

    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 1
    like_count = await db.fetchval(
        "SELECT COUNT(*) FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        persona_id,
    )
    assert like_count == 1


async def test_like_preset_records_like_without_db_persona(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    preset_id = PRESETS[0].id
    resp = await client.post(f"/personas/{preset_id}/like")
    assert resp.status_code == 204
    like_row = await db.fetchrow(
        "SELECT id FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        preset_id,
    )
    assert like_row is not None
    # Presets never get a personas row, so there is nothing to bump.
    persona_row = await db.fetchrow("SELECT id FROM personas WHERE id = $1", preset_id)
    assert persona_row is None


async def test_like_unknown_persona_is_404(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(f"/personas/{uuid.uuid4()}/like")
    assert resp.status_code == 404


async def test_like_other_users_private_persona_is_404(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = await _seed_other_user(db)
    persona_id = await _seed_persona(db, other_id, name="Hidden", is_public=False)
    resp = await client.post(f"/personas/{persona_id}/like")
    assert resp.status_code == 404
    like_row = await db.fetchrow("SELECT id FROM persona_likes WHERE persona_id = $1", persona_id)
    assert like_row is None
