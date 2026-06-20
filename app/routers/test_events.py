"""Telemetry endpoint contract tests.

The Slack contract is intentionally narrow: only allowlisted "human-meaningful" events get a Slack ping, and only when `APP_ENV=production`. Telemetry like `cold_start_complete` and `pitch_range` MUST persist to the DB but MUST NOT slack — otherwise the channel drowns in noise the moment more than a couple users connect."""

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_record_event_persists_row(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.post(
        "/events",
        json={
            "event_type": "cold_start_complete",
            "props": {"duration_ms": 1234, "phase_timings": {"first_audio_ms": 500}},
        },
    )
    assert resp.status_code == 204

    rows = await db.fetch("SELECT id, event_type, props FROM events WHERE user_id = $1", user["id"])
    assert len(rows) == 1
    assert rows[0]["event_type"] == "cold_start_complete"
    assert rows[0]["props"]["duration_ms"] == 1234
    # Regression: BIGINT autoincrement id must be assigned by the DB, not by the route.
    assert isinstance(rows[0]["id"], int)


async def test_slack_pings_for_allowlisted_event_in_production(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post(
            "/events", json={"event_type": "subscription_purchased", "props": {}}
        )
        assert resp.status_code == 204
    assert route.called
    body = route.calls.last.request.content.decode()
    assert "subscription_purchased" in body
    assert "C_TEST" in body
    get_settings.cache_clear()


async def test_slack_pings_for_session_error_with_reason(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    # A realtime session failure must reach Slack in production so a human sees a broken conversation live, with the reason attached (the audio WS is iOS↔provider direct, so this is the only server-side signal).
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post(
            "/events",
            json={
                "event_type": "session_error",
                "props": {"provider": "openai", "reason": "insufficient_quota"},
            },
        )
        assert resp.status_code == 204
    assert route.called
    body = route.calls.last.request.content.decode()
    assert "session_error" in body
    assert "insufficient_quota" in body
    get_settings.cache_clear()


async def test_slack_skips_for_telemetry_events_even_in_production(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The exact bug the user filed: dev sends a `cold_start_complete` and the channel pings with phase timings."""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        for telemetry_event in ("cold_start_complete", "pitch_range", "transcript_uploaded"):
            resp = await client.post(
                "/events",
                json={"event_type": telemetry_event, "props": {"duration_ms": 100}},
            )
            assert resp.status_code == 204
    assert not route.called, "telemetry event types must not Slack"
    get_settings.cache_clear()


async def test_slack_skips_in_dev_environment_even_for_allowlisted_events(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The other half of the user-filed bug: dev shares Slack creds with prd, so without the env gate, every dev session pollutes the prd channel."""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post(
            "/events", json={"event_type": "subscription_purchased", "props": {}}
        )
        assert resp.status_code == 204
    assert not route.called, "dev env must not Slack the prd channel"
    get_settings.cache_clear()


async def test_record_event_slack_skips_when_unconfigured(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "")
    get_settings.cache_clear()
    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        resp = await client.post(
            "/events", json={"event_type": "subscription_purchased", "props": {}}
        )
        assert resp.status_code == 204
    assert not route.called
    get_settings.cache_clear()
