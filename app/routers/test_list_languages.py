"""Integration tests for GET /languages."""

from httpx import AsyncClient

from app.profile.languages import LANGUAGES
from app.services.neon.rows import UserRow


async def test_list_languages_returns_full_catalog(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/languages")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == len(LANGUAGES)


async def test_list_languages_includes_english_with_accents(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/languages")
    by_name = {item["name"]: item for item in resp.json()}
    assert "English" in by_name
    assert len(by_name["English"]["accents"]) > 0
