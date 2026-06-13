"""Slack a #gtm ping when a user authenticates — the founder's real-time sign-in/up feed.

The auth method (Apple / Google / Email) is only known on the client, so iOS reports it here. Sign-in vs sign-up is decided server-side: a user row already in the DB means they're returning. Email arrives in two hops — a pre-auth "code requested" parent (the user has only typed their address, no account/JWT yet) and a post-verify reply — so the two read as one Slack thread.
"""

import logging
from typing import Literal

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel, Field

from app.auth.extract_bearer import extract_bearer
from app.auth.verify_clerk_jwt import verify_clerk_jwt
from app.config import get_settings
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.slack.post_message import post_message

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class AnnounceIn(BaseModel):
    method: str = Field(min_length=1, max_length=16)
    # requested = pre-auth email "code requested" (no JWT yet); succeeded/failed = the auth attempt's result.
    outcome: Literal["requested", "succeeded", "failed"] = "succeeded"
    thread_ts: str | None = None
    # The typed address, when known — labels the pre-auth request and any email-flow failure.
    pending_email: str | None = Field(default=None, max_length=320)
    # Holds the iOS `diagnoseAuthError` chain (underlying-error + Clerk fields), which is far longer than a bare message — too small a cap silently 422s the report and we lose the only window into a failure we can't reproduce. iOS caps its side at 1800.
    reason: str | None = Field(default=None, max_length=2000)


class AnnounceOut(BaseModel):
    thread_ts: str | None


@router.post("/announce", response_model=AnnounceOut)
async def announce_auth(
    body: AnnounceIn,
    authorization: str | None = Header(default=None),
    db: DBConn = Depends(get_neon_connection),
) -> AnnounceOut:
    settings = get_settings()

    if body.outcome == "requested":
        ts = await post_message(
            settings.slack_channel_gtm,
            f"{body.pending_email} requested an email sign-in code",
        )
        return AnnounceOut(thread_ts=ts)

    if body.outcome == "failed":
        # A failed attempt has no session, so no JWT to identify the user — fall back to the typed email or a placeholder. `<!channel>` pings the channel: a failed sign-in is a broken funnel worth interrupting for.
        who = body.pending_email or "Someone"
        suffix = f": {body.reason}" if body.reason else ""
        # The backend log is the real, queryable record of the failure (stdout → Fly logs / aggregator); Slack is only the human alert layered on top. WARNING because a dead sign-in is a broken funnel, not routine.
        logger.warning("sign-in failed: method=%s who=%s reason=%s", body.method, who, body.reason)
        ts = await post_message(
            settings.slack_channel_gtm,
            f"<!channel> {who} failed to sign in with {body.method}{suffix}",
            thread_ts=body.thread_ts,
        )
        return AnnounceOut(thread_ts=ts)

    claims = await verify_clerk_jwt(extract_bearer(authorization))
    clerk_user_id = claims.get("sub")
    if not isinstance(clerk_user_id, str):
        return AnnounceOut(thread_ts=None)
    raw_email = claims.get("email") or claims.get("primary_email_address")
    email = raw_email if isinstance(raw_email, str) else None
    # A row already present means a returning user; absent means this auth is creating them.
    exists = await db.fetchval("SELECT 1 FROM users WHERE clerk_user_id = $1", clerk_user_id)
    verb = "signed in" if exists else "signed up"
    label = email or clerk_user_id
    # No mention on success — it's a feed entry, not an alert.
    ts = await post_message(
        settings.slack_channel_gtm,
        f"{label} {verb} with {body.method}",
        thread_ts=body.thread_ts,
    )
    return AnnounceOut(thread_ts=ts)
