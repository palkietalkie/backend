"""Post a Slack message threaded under a conversation session's root message.

So one conversation's notifications (tool calls, session errors) collapse into a single Slack thread instead of scattering across the channel. The root is the first threadable event for a session; later events reply under its `ts`.

The session → root-ts map is in-process only. A restart or a second API machine forgets it, which at worst opens a second thread for an in-flight session (graceful, never an error). At one machine / one worker it's effectively always one thread; revisit with a shared store only if we run multiple API machines.
"""

from collections import OrderedDict

from app.services.slack.post_message import post_message

# Bounded so a long-lived process can't leak: sessions are short-lived, so once a session's events are done its entry is dead weight, evicted LRU.
_MAX_TRACKED_SESSIONS = 2048
_session_root_ts: OrderedDict[str, str] = OrderedDict()


def reset_session_threads() -> None:
    """Drop the in-process session → root-ts map. Used by tests for isolation; also a clean reset point if ever needed operationally."""
    _session_root_ts.clear()


async def post_session_threaded(channel: str, text: str, session_id: str | None) -> None:
    if session_id is None:
        await post_message(channel, text)
        return
    root_ts = _session_root_ts.get(session_id)
    if root_ts is not None:
        _session_root_ts.move_to_end(session_id)
        await post_message(channel, text, thread_ts=root_ts)
        return
    # First event for this session: it becomes the thread root. Only remember a ts Slack actually returned — a skipped/failed post (None) must not park a dangling pointer that later events would thread under.
    ts = await post_message(channel, text)
    if ts is not None:
        _session_root_ts[session_id] = ts
        _session_root_ts.move_to_end(session_id)
        while len(_session_root_ts) > _MAX_TRACKED_SESSIONS:
            _session_root_ts.popitem(last=False)
