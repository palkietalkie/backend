"""Client-side telemetry endpoint.

iOS posts events here so we can compute aggregate stats (e.g., cold-start percentiles) without paying for an external analytics vendor. Events land in the same `events` table backend pipelines write to, so dashboards can mix client and server signals."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow
from app.services.slack.format_event_props import format_event_props
from app.services.slack.format_user_label import format_user_label
from app.services.slack.post_session_threaded import post_session_threaded

router = APIRouter(prefix="/events", tags=["events"])


class EventIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=64)
    # Free-form structured payload. For cold-start: {"duration_ms": 5234, "phase_timings": {...}}.
    props: dict[str, Any] = Field(default_factory=lambda: {})
    # Optional client-side timestamp. Server stamps `ts` either way; this lets the client report when the event actually happened (handles offline replay).  # noqa: E501
    client_ts: datetime | None = None


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def record_event(
    body: EventIn,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> None:
    await db.execute(
        """INSERT INTO events (user_id, event_type, ts, props)
           VALUES ($1, $2, $3, $4)""",
        user["id"],
        body.event_type,
        body.client_ts or datetime.now(UTC),
        body.props,
    )

    # Slack only the small set of human-meaningful events from production. Telemetry like `pitch_range` and `cold_start_complete` belongs in a metrics dashboard, not a channel — Slacking them creates pure noise at low user counts. And dev events share the same Slack creds, so unfiltered we'd spam the GTM channel with every connected-device session.
    settings = get_settings()
    if settings.app_env == "production" and is_slack_worthy(body.event_type):
        text = (
            f":iphone: *{body.event_type}* — {format_user_label(user)} {format_event_props(body.props)}"
        ).rstrip()
        # Keep one conversation's events (tool calls, session errors) in a single Slack thread. Events without a session (signup, subscription) carry no sessionId and post standalone.
        raw_session = body.props.get("sessionId")
        session_id = raw_session if isinstance(raw_session, str) else None
        await post_session_threaded(settings.slack_channel_gtm, text, session_id)


# Curated list of events that ARE useful to see in Slack in real time. Telemetry (pitch_range, cold_start_complete, transcripts) explicitly excluded — those go to the events table for dashboards instead. Add an event here only when a human watching #gtm-prd would react to it.
_SLACK_WORTHY_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "user_signed_up",
        "subscription_purchased",
        "subscription_canceled",
        "premium_upgrade",
        "feedback_submitted",
        # A realtime session failed (WS error / abnormal disconnect). The events row in Neon is the durable record, but the audio WS is iOS↔provider direct so this is our only live signal a tester's conversation broke — Slack it so a human sees it now, not in a dashboard later. props carry provider + reason.
        "session_error",
        # The model called a realtime function tool (recall_*, web_fetch, end_conversation). The tool call rides the iOS↔provider WS directly and never hits the backend on its own, so iOS echoes each one here. end_conversation in particular silently hangs up the session — without this we have no signal whether the model ended a conversation vs the user leaving. props carry name + query.
        "tool_call",
    }
)


def is_slack_worthy(event_type: str) -> bool:
    """Whether an incoming event should be posted to Slack in real time (vs. only landing in the events table for dashboards)."""
    return event_type in _SLACK_WORTHY_EVENT_TYPES
