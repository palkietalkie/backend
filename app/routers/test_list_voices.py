"""Integration tests for GET /voices."""

from collections.abc import Generator

import pytest
from httpx import AsyncClient

from app.config import get_settings
from app.services.neon.rows import UserRow


@pytest.fixture
def openai_voices_provider(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    # Clear the settings cache before AND after — monkeypatch.setenv reverts the env at teardown, but `get_settings` is `lru_cache`d so the openai-flavored Settings object lingers and bleeds into the next test (test_voices.py asserts the PersonaPlex catalog and fails when the cache stays openai).
    monkeypatch.setenv("INFERENCE_PROVIDER", "openai")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_list_voices_returns_openai_catalog(
    app_with_overrides: tuple[AsyncClient, UserRow],
    openai_voices_provider: None,
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/voices")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) > 0
    first = body[0]
    assert {"id", "label", "gender", "description"} <= set(first.keys())
    assert first["gender"] in {"male", "female", "neutral"}
