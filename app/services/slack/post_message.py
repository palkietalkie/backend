"""Post a message to a Slack channel via chat.postMessage.

Single Slack auth path across the backend (same bot token / channel-id pattern as scripts/slack.sh — no incoming webhooks). Skips silently when the bot token or channel id is unset, so dev environments without Slack wired don't 5xx the caller. Slack outages are best-effort: logged, never propagated.
"""

import logging

import httpx

from app.config import get_settings

_logger = logging.getLogger(__name__)

_CHAT_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


async def post_message(channel: str, text: str, thread_ts: str | None = None) -> str | None:
    """Returns the posted message's `ts` (for threading replies under it), or None when skipped/failed."""
    settings = get_settings()
    # Only prd posts to Slack. Dev/test/local backends would spam the same channels with throwaway signups + sandbox webhook noise, drowning out real prd events.
    if settings.app_env != "production":
        return None
    if not settings.slack_bot_token or not channel:
        return None
    payload: dict[str, str] = {"channel": channel, "text": text}
    if thread_ts is not None:
        payload["thread_ts"] = thread_ts
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                _CHAT_POST_MESSAGE_URL,
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json=payload,
            )
        body = response.json()
        if not body.get("ok"):
            _logger.error("slack chat.postMessage rejected: %s", body.get("error", "unknown"))
            return None
        ts = body.get("ts")
        return ts if isinstance(ts, str) else None
    except httpx.HTTPError:
        _logger.exception("slack chat.postMessage failed (http)")
        return None
    except ValueError:
        _logger.exception("slack chat.postMessage failed (bad payload)")
        return None
