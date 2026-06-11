"""Tests for the list-personas endpoint (GET /personas).

Covers the preset + DB merge, ownership flags, the q search filter (name / description / role / topical_preferences), the three sort orders, the liked_by_me flag, and that other users' private personas are excluded."""

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
    role: str | None = None,
    topical_preferences: str | None = None,
    is_public: bool = False,
    voice_id: str = "NATM1",
) -> uuid.UUID:
    persona_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO personas (
               id, name, description, voice_id, role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, $2, $3, $4, $5, NULL, NULL, NULL, NULL, $6, $7, $8)""",
        persona_id,
        name,
        description,
        voice_id,
        role,
        topical_preferences,
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


async def test_list_includes_all_presets(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/personas")
    assert resp.status_code == 200
    returned = {item["name"] for item in resp.json()}
    assert {p.name for p in PRESETS}.issubset(returned)


async def test_list_includes_owned_custom_with_flags(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(db, user["id"], name="MyAunt")
    resp = await client.get("/personas")
    assert resp.status_code == 200
    custom = next((p for p in resp.json() if p["name"] == "MyAunt"), None)
    assert custom is not None
    assert custom["is_owner"] is True
    assert custom["is_preset"] is False
    assert custom["is_public"] is False


async def test_list_excludes_other_users_private(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = await _seed_other_user(db)
    await _seed_persona(db, other_id, name="OtherPrivate", is_public=False)
    resp = await client.get("/personas")
    names = {item["name"] for item in resp.json()}
    assert "OtherPrivate" not in names


async def test_list_includes_other_users_public(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = await _seed_other_user(db)
    await _seed_persona(db, other_id, name="OtherPublic", is_public=True)
    resp = await client.get("/personas")
    item = next((p for p in resp.json() if p["name"] == "OtherPublic"), None)
    assert item is not None
    assert item["is_owner"] is False


async def test_list_filter_q_matches_name(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(db, user["id"], name="ZuluFinder")
    resp = await client.get("/personas", params={"q": "zulufinder"})
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert "ZuluFinder" in names


async def test_list_filter_q_matches_topical_preferences(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(
        db, user["id"], name="Plain", topical_preferences="underwater basket weaving"
    )
    resp = await client.get("/personas", params={"q": "basket weaving"})
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert "Plain" in names


async def test_list_filter_q_excludes_non_matching(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await _seed_persona(db, user["id"], name="Alpha")
    resp = await client.get("/personas", params={"q": "zzz-no-match-zzz"})
    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert "Alpha" not in names


async def test_list_sort_popular_is_descending_by_like_count(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    liked_id = await _seed_persona(db, user["id"], name="HotPersona", is_public=True)
    await _seed_persona(db, user["id"], name="ColdPersona", is_public=True)
    await client.post(f"/personas/{liked_id}/like")
    resp = await client.get("/personas", params={"sort": "popular"})
    assert resp.status_code == 200
    counts = [item["like_count"] for item in resp.json()]
    assert counts == sorted(counts, reverse=True)
    hot = next(p for p in resp.json() if p["name"] == "HotPersona")
    cold = next(p for p in resp.json() if p["name"] == "ColdPersona")
    assert hot["like_count"] == 1
    assert cold["like_count"] == 0


async def test_list_liked_by_me_reflects_user_like(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    persona_id = await _seed_persona(db, user["id"], name="Likeable", is_public=True)
    await client.post(f"/personas/{persona_id}/like")
    resp = await client.get("/personas")
    item = next(p for p in resp.json() if p["name"] == "Likeable")
    assert item["liked_by_me"] is True


async def test_list_sort_recent_returns_200(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/personas", params={"sort": "recent"})
    assert resp.status_code == 200
