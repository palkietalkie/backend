from app.routers.record_event import is_slack_worthy


def test_session_error_is_slack_worthy() -> None:
    # A broken session is the other live signal that must page a human, not just sit in a dashboard.
    assert is_slack_worthy("session_error")


def test_high_volume_telemetry_is_not_slack_worthy() -> None:
    # Per-session telemetry would spam the channel at low user counts; it belongs in a metrics dashboard, not Slack.
    assert not is_slack_worthy("cold_start_complete")
    assert not is_slack_worthy("pitch_range")


def test_tool_call_is_slack_worthy() -> None:
    # The realtime WS is iOS↔provider direct, so a model tool call (recall_*, web_fetch, and especially end_conversation, which silently hangs up the session) never touches the backend otherwise. Slacking it live is our only window into what the model is actually doing mid-conversation.
    assert is_slack_worthy("tool_call")


def test_session_ended_is_durable_only_not_slack_worthy() -> None:
    # Every session emits one of these; Slacking them all would drown the channel. The value is the durable events-table row recording WHY the session ended (tool / cap / user-left), queried for the abnormal-end ratio, not a live ping.
    assert not is_slack_worthy("session_ended")
