from typing import Any


def format_event_props(props: dict[str, Any]) -> str:
    """Render an event's free-form `props` dict as Slack-flavored `\\`key=value\\`` segments.

    Empty props returns an empty string so the caller can `.rstrip()` cleanly. Values pass through `f"{v}"` so dicts and lists render as their Python repr — fine for our low-cardinality props (transactionId, persona_id, duration_ms). If a prop ever needs richer rendering, branch here.
    """
    if not props:
        return ""
    return " ".join(f"`{k}={v}`" for k, v in props.items())
