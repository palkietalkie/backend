"""Tests for the FastAPI factory create_app() — guards against router-registration regressions."""

from app.main import create_app


def test_create_app_has_health_route() -> None:
    # Enumerate via the OpenAPI schema: since fastapi 0.137 `app.routes` is a nested tree (internal detail), so flat iteration misses included routes.
    paths = set(create_app().openapi()["paths"])
    assert "/health" in paths


def test_create_app_registers_every_user_facing_router() -> None:
    """If a router import is accidentally removed from main.py, this trips."""
    paths = set(create_app().openapi()["paths"])
    # A representative cross-section of the routers — every key product surface.
    expected = {
        "/conversation/start",
        "/conversation/{session_id}/end",
        "/conversation/{session_id}/audio/mic",
        "/conversation/{session_id}/audio/model",
        "/personas",
        "/profile",
        "/profile/practice-options",
        "/stats",
        "/stats/mistakes",
        "/integrations",
        "/integrations/google-calendar/connect",
        "/integrations/google-calendar/callback",
        "/voices",
        "/languages",
        "/kg",
        "/recall/facts",
        "/recall/conversations",
        "/recall/transcripts",
        "/entitlement",
        "/plan_limits",
        "/events",
        "/webhooks/stripe",
        "/webhooks/apple/asn",
        "/consent",
    }
    missing = expected - paths
    assert not missing, f"missing routes: {missing}"


def test_create_app_returns_fresh_instances() -> None:
    # Factory => each call produces a distinct FastAPI for isolated dependency_overrides per test.
    assert create_app() is not create_app()


def test_create_app_title_and_version() -> None:
    app = create_app()
    assert app.title == "Palkie Talkie API"
    assert app.version == "0.1.0"


def test_web_fetch_route_is_registered() -> None:
    # main.py wires the recall/web_fetch endpoint that backs the realtime web_fetch tool.
    assert "/recall/web_fetch" in set(create_app().openapi()["paths"])
