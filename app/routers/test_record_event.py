from app.routers.record_event import is_slack_worthy


def test_experience_rating_is_slack_worthy() -> None:
    # The in-app "rate your experience" result must reach Slack, it's an early qualitative signal we want a human to see immediately (and Apple keeps public App Store ratings private from us).
    assert is_slack_worthy("experience_rating")


def test_session_error_is_slack_worthy() -> None:
    # A broken session is the other live signal that must page a human, not just sit in a dashboard.
    assert is_slack_worthy("session_error")


def test_high_volume_telemetry_is_not_slack_worthy() -> None:
    # Per-session telemetry would spam the channel at low user counts; it belongs in a metrics dashboard, not Slack.
    assert not is_slack_worthy("cold_start_complete")
    assert not is_slack_worthy("pitch_range")
