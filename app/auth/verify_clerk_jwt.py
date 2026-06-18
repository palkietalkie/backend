"""Verify a Clerk-issued session JWT and return its claims."""

from typing import Any

from fastapi import HTTPException, status
from jose import jwt
from jose.exceptions import JWTError

from app.auth.fetch_jwks import fetch_jwks
from app.auth.find_jwk_by_kid import find_jwk_by_kid
from app.config import get_settings


async def verify_clerk_jwt(token: str) -> dict[str, Any]:
    """Raises 401 on any failure (malformed header, missing kid, unknown kid, bad signature, expired, wrong issuer). Returns the raw claims dict — callers narrow individual fields via isinstance because JWT decode is opaque."""
    settings = get_settings()
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"malformed token header: {e}",
        ) from e

    raw_kid = header.get("kid")
    if not isinstance(raw_kid, str) or not raw_kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing kid in token header",
        )
    kid: str = raw_kid

    jwks = await fetch_jwks()
    key = find_jwk_by_kid(jwks, kid)
    if key is None:
        # Cached JWKS predates a Clerk key rotation; refetch once before giving up so a rotation doesn't 401 every request until the cache TTL expires.
        jwks = await fetch_jwks(force=True)
        key = find_jwk_by_kid(jwks, kid)
    if key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unknown kid in token header",
        )

    raw_alg = header.get("alg", "RS256")
    alg: str = raw_alg if isinstance(raw_alg, str) else "RS256"

    try:
        # Clerk session tokens don't always carry aud; verifying it would 401 every request.
        decoded = jwt.decode(
            token,
            key,
            algorithms=[alg],
            issuer=settings.clerk_issuer,
            options={"verify_aud": False},
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"token verification failed: {e}",
        ) from e
    assert isinstance(decoded, dict), f"jwt.decode returned {type(decoded).__name__}"
    return decoded
