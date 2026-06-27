import pytest

from app.services.slack import post_session_threaded as mod
from app.services.slack.post_session_threaded import post_session_threaded


def _spy_post(
    monkeypatch: pytest.MonkeyPatch, ts_returns: list[str | None]
) -> list[tuple[str, str, str | None]]:
    """Replace post_message with a spy that records (channel, text, thread_ts) and returns the next canned ts (simulating prod, where post_message returns the posted message's ts)."""
    calls: list[tuple[str, str, str | None]] = []
    seq = iter(ts_returns)

    async def _fake(channel: str, text: str, thread_ts: str | None = None) -> str | None:
        calls.append((channel, text, thread_ts))
        return next(seq)

    monkeypatch.setattr(mod, "post_message", _fake)
    return calls


async def test_first_event_posts_root_and_later_events_reply_in_its_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mod.reset_session_threads()
    calls = _spy_post(monkeypatch, ["111.1", "222.2"])
    await post_session_threaded("#gtm", "tool_call recall_facts", "sess-A")
    await post_session_threaded("#gtm", "session_error ws_closed", "sess-A")
    assert calls[0][2] is None, "the first event opens the thread, so it posts with no thread_ts"
    assert calls[1][2] == "111.1", "a later event for the same session replies under the root's ts"


async def test_each_session_gets_its_own_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.reset_session_threads()
    calls = _spy_post(monkeypatch, ["111.1", "999.9"])
    await post_session_threaded("#gtm", "a", "sess-A")
    await post_session_threaded("#gtm", "b", "sess-B")
    assert calls[1][2] is None, "a different session opens its own root, not threaded under another"


async def test_no_session_id_posts_standalone(monkeypatch: pytest.MonkeyPatch) -> None:
    mod.reset_session_threads()
    calls = _spy_post(monkeypatch, ["111.1"])
    await post_session_threaded("#gtm", "user_signed_up", None)
    assert calls[0][2] is None, "events without a session (signup, subscription) never thread"


async def test_a_dropped_root_post_does_not_leave_a_dangling_thread_pointer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # post_message returns None when Slack is skipped/failed (e.g. non-prod, outage). If we stored that as the root, later events would thread under a non-existent message. The next event must instead open a fresh root.
    mod.reset_session_threads()
    calls = _spy_post(monkeypatch, [None, "333.3"])
    await post_session_threaded("#gtm", "first", "sess-A")
    await post_session_threaded("#gtm", "second", "sess-A")
    assert calls[1][2] is None, "no root was recorded, so the next event opens the thread itself"
