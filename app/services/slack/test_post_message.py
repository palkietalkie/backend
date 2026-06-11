"""Tests for the Slack post_message helper."""

import json

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


async def test_skips_when_not_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        await post_message("C0B8R2H1E8H", "hi")
    assert not route.called


async def test_skips_when_bot_token_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "")
    monkeypatch.setenv("SLACK_CHANNEL_GTM", "C0B8R2H1E8H")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        await post_message("C0B8R2H1E8H", "hi")
    assert not route.called


async def test_skips_when_channel_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage")
        await post_message("", "hi")
    assert not route.called


async def test_posts_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
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


async def test_returns_ts_so_callers_can_thread_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    # The ts is the handle a follow-up reply threads under; post_message must surface it on success.
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "1700000000.000100"})
        )
        ts = await post_message("C0B8R2H1E8H", "hi")
    assert ts == "1700000000.000100"


async def test_returns_none_when_ts_missing_or_non_string(monkeypatch: pytest.MonkeyPatch) -> None:
    # Slack normally returns a string ts; defend against a malformed/absent value rather than handing callers a non-str.
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": 12345})
        )
        ts = await post_message("C0B8R2H1E8H", "hi")
    assert ts is None


async def test_threads_reply_when_thread_ts_given(monkeypatch: pytest.MonkeyPatch) -> None:
    # A provided thread_ts must travel in the payload so the reply nests under the parent message.
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "1700000000.000200"})
        )
        await post_message("C0B8R2H1E8H", "reply", thread_ts="1700000000.000100")
    body = json.loads(route.calls.last.request.content)
    assert body["thread_ts"] == "1700000000.000100"


async def test_omits_thread_ts_when_not_threading(monkeypatch: pytest.MonkeyPatch) -> None:
    # A top-level post must NOT carry thread_ts, otherwise Slack would try to nest it under a missing parent.
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        route = router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": True, "ts": "1700000000.000300"})
        )
        await post_message("C0B8R2H1E8H", "top-level")
    body = json.loads(route.calls.last.request.content)
    assert "thread_ts" not in body


async def test_logs_when_slack_returns_not_ok(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            return_value=httpx.Response(200, json={"ok": False, "error": "channel_not_found"})
        )
        with caplog.at_level("ERROR"):
            ts = await post_message("C_BAD", "hi")
    assert "channel_not_found" in caplog.text
    # A rejected post yields no ts, so callers don't try to thread under a message that never landed.
    assert ts is None


async def test_swallows_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    get_settings.cache_clear()
    with respx.mock(base_url="https://slack.com", assert_all_called=False) as router:
        router.post("/api/chat.postMessage").mock(
            side_effect=httpx.ConnectError("boom"),
        )
        # Should NOT raise.
        await post_message("C0B8R2H1E8H", "hi")
