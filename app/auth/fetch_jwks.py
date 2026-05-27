"""Fetch Clerk's JWKS with a 1h in-memory cache."""

import time

import httpx

from app.auth.jwk import JWKS
from app.config import get_settings

_cached_jwks: JWKS | None = None
_fetched_at: float = 0.0
_TTL_SECONDS = 3600


async def fetch_jwks() -> JWKS:
    """Returns cached JWKS (JSON Web Key Set) or fetches fresh. Concurrent callers may double-fetch once; cost is bounded by Clerk's edge cache."""
    global _cached_jwks, _fetched_at
    now = time.time()
    if _cached_jwks is not None and now - _fetched_at < _TTL_SECONDS:
        return _cached_jwks

    settings = get_settings()
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(settings.clerk_jwks_url)
        resp.raise_for_status()
        jwks: JWKS = resp.json()

    _cached_jwks = jwks
    _fetched_at = now
    return jwks
