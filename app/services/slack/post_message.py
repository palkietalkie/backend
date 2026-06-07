"""Post a message to a Slack channel via chat.postMessage.

Single Slack auth path across the backend (same bot token / channel-id pattern as scripts/slack.sh — no incoming webhooks). Skips silently when the bot token or channel id is unset, so dev environments without Slack wired don't 5xx the caller. Slack outages are best-effort: logged, never propagated.
"""

import logging

import httpx

from app.config import get_settings

_logger = logging.getLogger(__name__)

_CHAT_POST_MESSAGE_URL = "https://slack.com/api/chat.postMessage"


async def post_message(channel: str, text: str) -> None:
    settings = get_settings()
    if not settings.slack_bot_token or not channel:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                _CHAT_POST_MESSAGE_URL,
                headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
                json={"channel": channel, "text": text},
            )
        body = response.json()
        if not body.get("ok"):
            _logger.error("slack chat.postMessage rejected: %s", body.get("error", "unknown"))
    except httpx.HTTPError:
        _logger.exception("slack chat.postMessage failed (http)")
    except ValueError:
        _logger.exception("slack chat.postMessage failed (bad payload)")
