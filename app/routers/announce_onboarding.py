"""Slack a #gtm thread tracking a user's walk through onboarding — the founder's real-time drop-off feed.

iOS reports each step the moment it's viewed and again when completed. The first report (no thread_ts) opens a thread headed "started setup"; every later report replies under it, so one user's whole onboarding reads as a single collapsible thread instead of flooding the channel. Which step / phase is only known on the client, so iOS sends them; the user is identified from the JWT (+ the name iOS passes, since the JWT often omits it).
"""

from typing import Literal

from fastapi import APIRouter, Header
from pydantic import BaseModel, Field

from app.auth.extract_bearer import extract_bearer
from app.auth.verify_clerk_jwt import verify_clerk_jwt
from app.config import get_settings
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


class OnboardingAnnounceIn(BaseModel):
    step: str = Field(min_length=1, max_length=40)
    phase: Literal["viewed", "completed"]
    thread_ts: str | None = None
    preferred_name: str | None = Field(default=None, max_length=200)


class OnboardingAnnounceOut(BaseModel):
    thread_ts: str | None


@router.post("/announce", response_model=OnboardingAnnounceOut)
async def announce_onboarding(
    body: OnboardingAnnounceIn,
    authorization: str | None = Header(default=None),
) -> OnboardingAnnounceOut:
    settings = get_settings()
    claims = await verify_clerk_jwt(extract_bearer(authorization))
    clerk_user_id = claims.get("sub")
    if not isinstance(clerk_user_id, str):
        return OnboardingAnnounceOut(thread_ts=None)
    raw_email = claims.get("email") or claims.get("primary_email_address")
    email = raw_email if isinstance(raw_email, str) else None
    who = body.preferred_name or email or clerk_user_id

    emoji = "👀" if body.phase == "viewed" else "✅"
    line = f"{emoji} {body.phase}: {body.step}"
    # First report opens the thread with a header; the rest reply under it (no header) so the channel shows one line per user, expandable.
    text = line if body.thread_ts else f"🚀 {who} started setup\n{line}"
    ts = await post_message(settings.slack_channel_gtm, text, thread_ts=body.thread_ts)
    return OnboardingAnnounceOut(thread_ts=ts)
