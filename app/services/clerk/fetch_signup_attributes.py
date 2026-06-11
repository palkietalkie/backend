"""Read a live Clerk instance's sign-up attribute settings from its public Frontend API."""

from typing import Any

import httpx

from app.services.clerk.get_clerk_frontend_api_url import get_clerk_frontend_api_url


async def fetch_signup_attributes(publishable_key: str) -> dict[str, Any]:
    # /v1/environment is the same unauthenticated endpoint the Clerk JS/iOS SDKs read on boot; user_settings.attributes is the source of truth for which fields a sign-up requires.
    base = get_clerk_frontend_api_url(publishable_key)
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{base}/v1/environment", params={"_clerk_js_version": "5"})
    resp.raise_for_status()
    payload: Any = resp.json()
    # Missing keys raise KeyError here, which is the failure we want to surface; the annotation pins the JSON `Any` to the shape callers read.
    attributes: dict[str, Any] = payload["user_settings"]["attributes"]
    return attributes
