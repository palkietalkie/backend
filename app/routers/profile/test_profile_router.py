"""Tests for /profile endpoints."""

from typing import Any

import pytest
from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_fetch_profile_returns_user_fields(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, user = app_with_overrides
    resp = await client.get("/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["preferred_name"] == user["preferred_name"]
    assert body["native_languages"] == user["native_languages"]


async def test_list_practice_options_exposes_enums(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/profile/practice-options")
    assert resp.status_code == 200
    body = resp.json()
    assert "beginner" in body["proficiency"]
    assert "normal" in body["tutor_speaking_speed"]
    # Speed playback rates are served from the backend (SSoT) so the picker shows the concrete multiplier, which disambiguates "slow" vs "very slow" (vague as words). Every slug has a rate; normal is 1.0; rates increase slow→fast.
    rates = body["tutor_speaking_speed_rates"]
    assert set(rates) == set(body["tutor_speaking_speed"])
    assert rates["normal"] == 1.0
    assert rates["very_slow"] < rates["slow"] < rates["normal"] < rates["fast"] < rates["very_fast"]
    # Goal presets are served here too (SSoT) so iOS renders chips without hardcoding the list.
    assert "dating_relationships" in body["goals"]
    assert "studying_abroad" in body["goals"]


async def test_update_profile_patches_fields(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.patch(
        "/profile",
        json={"preferred_name": "Wes", "location_city": "San Francisco"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["preferred_name"] == "Wes"
    assert body["location_city"] == "San Francisco"


async def test_update_profile_does_not_auto_fill_pronunciation_on_save(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
) -> None:
    """PATCH must leave `name_pronunciation` exactly as the user sent it. Pronunciation suggestions live behind GET /profile (as a placeholder), not behind PATCH."""
    client, user = app_with_overrides
    await db.execute("UPDATE users SET name_pronunciation = NULL WHERE id = $1", user["id"])
    resp = await client.patch("/profile", json={"preferred_name": "Wey"})
    assert resp.status_code == 200
    assert resp.json()["name_pronunciation"] in (None, "")
    persisted = await db.fetchval("SELECT name_pronunciation FROM users WHERE id = $1", user["id"])
    assert persisted is None


async def test_update_profile_rejects_invalid_language_accent_pair(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    # "Kansai" is a real accent (Japanese) so Pydantic accepts it — the rejection must come from our cross-field validator, not from Literal parsing (a malformed string would 422 too early).
    resp = await client.patch(
        "/profile",
        json={"target_language": "English", "target_accents": ["Kansai"]},
    )
    assert resp.status_code == 422


async def test_update_profile_accent_only_validated_against_stored_language(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    # Stored target_language defaults to English; a valid-but-foreign accent (Kansai is Japanese) is rejected against it → 422. Exercises the handler's accent loop, not the Pydantic layer.
    client, _ = app_with_overrides
    resp = await client.patch("/profile", json={"target_accents": ["Kansai"]})
    assert resp.status_code == 422


async def test_update_profile_accepts_accent_only_valid_for_stored_language(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    # Accent-only PATCH whose accents are all valid for the stored language (English) succeeds and persists — the loop completes without rejecting.
    client, _ = app_with_overrides
    resp = await client.patch("/profile", json={"target_accents": ["American", "British"]})
    assert resp.status_code == 200
    assert resp.json()["target_accents"] == ["American", "British"]


async def test_update_profile_rejects_when_stored_language_unrecognized(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
) -> None:
    # Defensive guard that replaced an unsafe type-narrowing shortcut: a corrupt/legacy stored language returns a clean 422, not the 500 a blind narrow would have produced when get_language raised KeyError.
    client, user = app_with_overrides
    await db.execute("UPDATE users SET target_language = 'Wakandan' WHERE id = $1", user["id"])
    resp = await client.patch("/profile", json={"target_accents": ["Kansai"]})
    assert resp.status_code == 422


async def test_update_profile_accepts_multiple_accents(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.patch(
        "/profile",
        json={
            "target_language": "English",
            "target_accents": ["American", "British", "Australian"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_accents"] == ["American", "British", "Australian"]


async def test_fetch_profile_returns_all_persisted_accents(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    """Regression: user reported that after saving multiple accents, the next GET shows only one. PATCH then GET on the same connection should return every accent saved."""
    client, _ = app_with_overrides
    patch_resp = await client.patch(
        "/profile",
        json={
            "target_language": "English",
            "target_accents": ["American", "British", "Australian"],
        },
    )
    assert patch_resp.status_code == 200
    get_resp = await client.get("/profile")
    assert get_resp.status_code == 200
    assert get_resp.json()["target_accents"] == ["American", "British", "Australian"]


async def test_fetch_profile_returns_suggestion_when_pronunciation_empty(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When `name_pronunciation` is empty, GET /profile returns a Gemma-generated `name_pronunciation_suggestion` as a placeholder hint without persisting it. Stored field stays empty so user-driven clears are respected."""
    from app.routers.profile import fetch_profile as fetch_profile_mod

    async def _guess(preferred_name: str, _target_language: str) -> str:
        return f"{preferred_name.upper()}-suggested"

    monkeypatch.setattr(fetch_profile_mod, "guess_name_pronunciation", _guess)
    client, user = app_with_overrides
    await db.execute("UPDATE users SET name_pronunciation = NULL WHERE id = $1", user["id"])
    resp = await client.get("/profile")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name_pronunciation"] in (None, "")
    preferred_name = user["preferred_name"] or ""
    assert body["name_pronunciation_suggestion"] == f"{preferred_name.upper()}-suggested"
    persisted = await db.fetchval("SELECT name_pronunciation FROM users WHERE id = $1", user["id"])
    assert persisted is None


async def test_update_profile_null_pronunciation_keeps_existing(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
) -> None:
    """PATCH contract: an explicit `null` for `name_pronunciation` means "keep the existing value" (standard COALESCE semantics). iOS clearing the field must send `""` instead of `null`, otherwise the clear is silently ignored. This regression test documents that contract."""
    client, user = app_with_overrides
    await db.execute("UPDATE users SET name_pronunciation = 'WAY-yu' WHERE id = $1", user["id"])
    resp = await client.patch("/profile", json={"name_pronunciation": None})
    assert resp.status_code == 200
    persisted = await db.fetchval("SELECT name_pronunciation FROM users WHERE id = $1", user["id"])
    assert persisted == "WAY-yu"


async def test_update_profile_respects_explicit_empty_pronunciation(
    app_with_overrides: tuple[AsyncClient, UserRow],
    db: DBConn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: clearing the pronunciation field and saving must persist the clear. Previously an over-eager auto-fill on PATCH wrote a Gemma guess right back, so the value reappeared on the next visit."""
    from app.routers.profile import fetch_profile as fetch_profile_mod

    async def _guess(*_a: Any, **_k: Any) -> str:
        return "AUTO-FILLED"

    monkeypatch.setattr(fetch_profile_mod, "guess_name_pronunciation", _guess)
    client, user = app_with_overrides
    await db.execute("UPDATE users SET name_pronunciation = 'WAY-yu' WHERE id = $1", user["id"])
    resp = await client.patch("/profile", json={"name_pronunciation": ""})
    assert resp.status_code == 200
    assert resp.json()["name_pronunciation"] in (None, "")
    persisted = await db.fetchval("SELECT name_pronunciation FROM users WHERE id = $1", user["id"])
    assert persisted in (None, "")


async def test_list_languages_endpoint_returns_known_languages(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/languages")
    assert resp.status_code == 200
    body = resp.json()
    names = {item["name"] for item in body}
    assert "English" in names
    assert "Japanese" in names
