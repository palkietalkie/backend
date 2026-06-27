"""Fetch a user's email + first name from Clerk's Backend API, to backfill a JIT user row that Apple/Google sign-in left without a profile (the session JWT omits email + name on the Apple path)."""

from dataclasses import dataclass

import httpx
from pydantic import ValidationError

from app.services.clerk.clerk_user_payload import ClerkUserPayload
from app.services.clerk.parse_first_name import parse_first_name
from app.services.clerk.parse_primary_email import parse_primary_email


@dataclass(frozen=True)
class ClerkUserProfile:
    email: str | None
    # First name only: preferred_name is how the tutor addresses the user ("Hey Taka"), not their full legal name.
    first_name: str | None


async def fetch_clerk_user(clerk_user_id: str, secret_key: str) -> ClerkUserProfile | None:
    """Returns the user's email + first name, or None on any failure so a Clerk hiccup never breaks the request that triggered the backfill."""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(
                f"https://api.clerk.com/v1/users/{clerk_user_id}",
                headers={"Authorization": f"Bearer {secret_key}"},
            )
        resp.raise_for_status()
        payload = ClerkUserPayload.model_validate(resp.json())
    except httpx.HTTPError, ValidationError:
        return None
    return ClerkUserProfile(
        email=parse_primary_email(payload), first_name=parse_first_name(payload)
    )
