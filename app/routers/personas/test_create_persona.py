"""Tests for the create-persona endpoint (POST /personas).

Exercises row persistence + ownership stamping, the PersonaOut shape returned to the client, and the voice-id validation gate."""

import uuid

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_create_persona_persists_owned_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.post(
        "/personas",
        json={
            "name": "MyCoach",
            "description": "personal coach",
            "voice_id": "NATM1",
            "role": "coach",
            "age": "40s",
            "background": "ex-athlete",
            "vocabulary_register": "casual",
            "conversational_style": "warm",
            "topical_preferences": "training",
            "is_public": False,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "MyCoach"
    assert body["role"] == "coach"
    assert body["is_owner"] is True
    assert body["is_preset"] is False
    assert body["like_count"] == 0
    assert body["liked_by_me"] is False

    row = await db.fetchrow(
        "SELECT name, role, is_public, user_id, like_count FROM personas WHERE id = $1",
        uuid.UUID(body["id"]),
    )
    assert row is not None
    assert row["user_id"] == user["id"]
    assert row["name"] == "MyCoach"
    assert row["role"] == "coach"
    assert row["is_public"] is False
    assert row["like_count"] == 0


async def test_create_persona_defaults_optional_fields_to_null(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/personas",
        json={"name": "Minimal", "voice_id": "NATM1"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["description"] == ""
    assert body["role"] is None
    assert body["is_public"] is False

    row = await db.fetchrow(
        "SELECT description, role, background FROM personas WHERE id = $1",
        uuid.UUID(body["id"]),
    )
    assert row is not None
    assert row["description"] == ""
    assert row["role"] is None
    assert row["background"] is None


async def test_create_persona_rejects_unknown_voice(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/personas",
        json={"name": "Bad", "description": "", "voice_id": "NOT_A_VOICE"},
    )
    assert resp.status_code == 400
    # The failed validation must not have written a row.
    row = await db.fetchrow("SELECT id FROM personas WHERE name = $1", "Bad")
    assert row is None


async def test_create_persona_rejects_empty_name(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/personas",
        json={"name": "", "voice_id": "NATM1"},
    )
    assert resp.status_code == 422
