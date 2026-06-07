"""Telemetry endpoint contract tests."""

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


async def test_record_event_pings_slack(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()

    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        resp = await client.post(
            "/events", json={"event_type": "conversation_started", "props": {"persona_id": "abc"}}
        )
        assert resp.status_code == 204
    assert route.called
    body = route.calls.last.request.content.decode()
    assert "conversation_started" in body
    assert "C_TEST" in body
    get_settings.cache_clear()


async def test_record_event_slack_skips_when_unconfigured(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "")
    get_settings.cache_clear()
    client, _ = app_with_overrides
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        resp = await client.post("/events", json={"event_type": "foo"})
        assert resp.status_code == 204
    assert not route.called
    get_settings.cache_clear()
