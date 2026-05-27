"""Smoke tests. No external services touched."""

from pathlib import Path

import pytest
from httpx import AsyncClient
from starlette.routing import Route


def test_app_imports() -> None:
    from app.main import app

    assert app.title == "Palkie Talkie API"


def test_routes_registered() -> None:
    from app.main import app

    paths = {route.path for route in app.routes if isinstance(route, Route)}
    expected = {
        "/health",
        "/conversation/start",
        "/conversation/{session_id}/transcript",
        "/conversation/{session_id}/end",
        "/webhooks/stripe",
        "/webhooks/apple/asn",
        "/entitlement",
        "/personas",
        "/stats",
        "/stats/mistakes",
        "/stats/phrases",
        "/stats/cefr",
        "/integrations/google-calendar/connect",
        "/profile",
        "/kg",
        "/content/today",
        "/devices/apns",
    }
    missing = expected - paths
    assert not missing, f"missing routes: {missing}"


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Default settings (no env, no .env) — ``app_env`` defaults to ``development``."""
    from app.config import Settings, get_settings

    # Wipe every env var Settings reads so we observe the dataclass defaults
    for name in (
        "APP_ENV",
        "LOG_LEVEL",
        "NEON_DATABASE_URL",
        "PERSONAPLEX_HOST",
        "PERSONAPLEX_PORT",
        "PERSONAPLEX_SCHEME",
    ):
        monkeypatch.delenv(name, raising=False)
    # chdir to a clean tmp dir so Pydantic Settings doesn't pick up the project's .env.
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    s = Settings()
    assert s.app_env == "development"
    assert "127.0.0.1" in s.personaplex_ws_url
    get_settings.cache_clear()


async def test_health_endpoint(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
