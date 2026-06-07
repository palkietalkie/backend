"""Tests for the Slack post_message helper."""

import httpx
import pytest
import respx

from app.config import get_settings
from app.services.slack.post_message import post_message


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


async def test_skips_when_bot_token_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C0B8R2H1E8H")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        await post_message("C0B8R2H1E8H", "hi")
    assert not route.called


async def test_skips_when_channel_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        await post_message("", "hi")
    assert not route.called


async def test_posts_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True})
        )
        await post_message("C0B8R2H1E8H", "hi")
    assert route.called
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer xoxb-test"
    assert request.headers["content-type"] == "application/json"


async def test_logs_when_slack_returns_not_ok(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        )
        with caplog.at_level("ERROR"):
            await post_message("C_BAD", "hi")
    assert "channel_not_found" in caplog.text


async def test_swallows_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            side_effect=httpx.ConnectError("boom"),
        )
        # Should NOT raise.
        await post_message("C0B8R2H1E8H", "hi")
