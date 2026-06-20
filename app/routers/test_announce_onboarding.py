"""Tests for /onboarding/announce — the onboarding drop-off Slack thread. verify_clerk_jwt is monkeypatched; Slack is mocked with respx."""

from typing import Any

import httpx
import pytest
import respx
from httpx import AsyncClient

from app.config import get_settings
from app.routers import announce_onboarding as mod
from app.services.neon.rows import UserRow


def _enable_prod_slack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C_TEST")
    get_settings.cache_clear()


def _patch_jwt(monkeypatch: pytest.MonkeyPatch, email: str | None) -> None:
    async def _verify(_token: str) -> dict[str, Any]:
        return {"sub": "user_abc", "email": email}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _verify)


async def test_first_event_opens_a_thread_with_a_header(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    _patch_jwt(monkeypatch, None)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "100.1"})
        )
        resp = await client.post(
            "/onboarding/announce",
            headers={"Authorization": "Bearer t"},
            json={"step": "displayLanguage", "phase": "viewed", "preferred_name": "Wes Nishio"},
        )
    assert resp.status_code == 200
    assert resp.json()["thread_ts"] == "100.1"
    sent = route.calls.last.request.content.decode()
    assert "Wes Nishio started setup" in sent
    assert "viewed: displayLanguage" in sent
    get_settings.cache_clear()


async def test_later_event_threads_without_a_new_header(
    app_with_overrides: tuple[AsyncClient, UserRow], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, _ = app_with_overrides
    _enable_prod_slack(monkeypatch)
    _patch_jwt(monkeypatch, None)
    with respx.mock(base_url="https://slack.com") as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "100.2"})
        )
        resp = await client.post(
            "/onboarding/announce",
            headers={"Authorization": "Bearer t"},
            json={"step": "goals", "phase": "completed", "thread_ts": "100.1"},
        )
    assert resp.status_code == 200
    sent = route.calls.last.request.content.decode()
    assert "completed: goals" in sent
    assert "started setup" not in sent, "replies must not repeat the thread header"
    assert "100.1" in sent, "must thread under the parent ts"
    get_settings.cache_clear()
