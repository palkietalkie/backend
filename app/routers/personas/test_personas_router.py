"""Integration tests for the personas router (list / create / update / delete / like / unlike).

The conftest seeds a `fake_user` and overrides `resolve_current_user` so every call here uses that user's id. The persona-likes denormalized count and the preset / DB merge logic are the hot spots being exercised."""

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


async def test_list_personas_includes_all_presets(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/personas")
    assert resp.status_code == 200
    body = resp.json()
    preset_names = {p.name for p in PRESETS}
    returned_names = {item["name"] for item in body}
    assert preset_names.issubset(returned_names)


async def test_list_personas_includes_user_custom_personas(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(db, user["id"], name="MyAunt")
    resp = await client.get("/personas")
    assert resp.status_code == 200
    body = resp.json()
    custom = next((p for p in body if p["name"] == "MyAunt"), None)
    assert custom is not None
    assert custom["is_owner"] is True
    assert custom["is_preset"] is False


async def test_list_personas_filter_by_q(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(db, user["id"], name="ZuluFinder")
    resp = await client.get("/personas", params={"q": "zulufinder"})
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert "ZuluFinder" in names


async def test_list_personas_sort_popular(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/personas", params={"sort": "popular"})
    assert resp.status_code == 200
    body = resp.json()
    counts = [item["like_count"] for item in body]
    assert counts == sorted(counts, reverse=True) or len(set(counts)) == 1


async def test_list_personas_sort_recent(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/personas", params={"sort": "recent"})
    assert resp.status_code == 200


async def test_list_personas_excludes_other_users_private(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _user = app_with_overrides
    # Seed a different user and their private persona.
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)""",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    await _seed_persona(db, other_id, name="OtherPrivate", is_public=False)
    resp = await client.get("/personas")
    names = {item["name"] for item in resp.json()}
    assert "OtherPrivate" not in names


async def test_create_persona_persists_row(
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
            "background": "BG",
            "vocabulary_register": "casual",
            "conversational_style": "warm",
            "topical_preferences": "training",
            "is_public": False,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "MyCoach"
    assert body["is_owner"] is True
    assert body["is_preset"] is False
    row = await db.fetchrow(
        "SELECT name, user_id FROM personas WHERE id = $1", uuid.UUID(body["id"])
    )
    assert row is not None
    assert row["user_id"] == user["id"]


async def test_create_persona_rejects_unknown_voice(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(
        "/personas",
        json={"name": "X", "description": "", "voice_id": "NOT_A_VOICE"},
    )
    assert resp.status_code == 400


async def test_update_persona_writes_fields(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="Original")
    resp = await client.patch(
        f"/personas/{persona_id}",
        json={"name": "Renamed", "description": "new desc"},
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Renamed"


async def test_update_persona_rejects_preset(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    preset_id = PRESETS[0].id
    resp = await client.patch(f"/personas/{preset_id}", json={"name": "Hijack"})
    assert resp.status_code == 403


async def test_update_persona_rejects_other_users(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)""",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    persona_id = await _seed_persona(db, other_id, name="Theirs", is_public=True)
    resp = await client.patch(f"/personas/{persona_id}", json={"name": "Hijack"})
    assert resp.status_code == 404


async def test_update_persona_validates_voice_id(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"])
    resp = await client.patch(f"/personas/{persona_id}", json={"voice_id": "BOGUS"})
    assert resp.status_code == 400


async def test_update_persona_no_op_when_body_empty(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="StayPut")
    resp = await client.patch(f"/personas/{persona_id}", json={})
    assert resp.status_code == 200
    assert resp.json()["name"] == "StayPut"


async def test_delete_persona_removes_row(
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
    preset_id = PRESETS[0].id
    resp = await client.delete(f"/personas/{preset_id}")
    assert resp.status_code == 403


async def test_delete_persona_rejects_other_users(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)""",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    persona_id = await _seed_persona(db, other_id, name="Theirs", is_public=True)
    resp = await client.delete(f"/personas/{persona_id}")
    assert resp.status_code == 404


async def test_like_persona_bumps_count(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _user = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)""",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    persona_id = await _seed_persona(db, other_id, name="Public", is_public=True)
    resp = await client.post(f"/personas/{persona_id}/like")
    assert resp.status_code == 204
    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 1


async def test_like_persona_is_idempotent(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    await client.post(f"/personas/{persona_id}/like")
    await client.post(f"/personas/{persona_id}/like")
    row = await db.fetchrow("SELECT like_count FROM personas WHERE id = $1", persona_id)
    assert row is not None
    assert row["like_count"] == 1


async def test_like_persona_preset_inserts_like_without_db_persona(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    preset_id = PRESETS[0].id
    resp = await client.post(f"/personas/{preset_id}/like")
    assert resp.status_code == 204
    row = await db.fetchrow(
        "SELECT id FROM persona_likes WHERE user_id = $1 AND persona_id = $2",
        user["id"],
        preset_id,
    )
    assert row is not None


async def test_like_persona_404s_unknown(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.post(f"/personas/{uuid.uuid4()}/like")
    assert resp.status_code == 404


async def test_like_persona_404s_private_other_user(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, premium) VALUES ($1, $2, FALSE)""",
        other_id,
        f"u_other_{other_id.hex[:8]}",
    )
    persona_id = await _seed_persona(db, other_id, name="Hidden", is_public=False)
    resp = await client.post(f"/personas/{persona_id}/like")
    assert resp.status_code == 404


async def test_unlike_persona_drops_count(
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


async def test_unlike_when_not_liked_is_noop(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], is_public=True)
    resp = await client.delete(f"/personas/{persona_id}/like")
    assert resp.status_code == 204
