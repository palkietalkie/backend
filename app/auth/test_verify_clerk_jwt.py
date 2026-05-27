"""Tests for verify_clerk_jwt + resolve_current_user.

We mint short-lived RS256 tokens signed by an ephemeral key whose JWK we serve to the verifier via respx, then assert the verifier returns the parsed claims on success and raises 401 on tampered tokens / missing kid / unknown kid. resolve_current_user is exercised separately by stubbing verify_clerk_jwt — the JWT path itself is covered above.
"""

import base64
import time
import uuid
from typing import Any

import httpx
import pytest
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from jose import jwt

from app.auth import fetch_jwks, resolve_current_user, verify_clerk_jwt


def _b64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _sign(
    claims: dict[str, Any], private_key_pem: bytes, kid: str = "test-kid-1"
) -> str:
    return jwt.encode(
        claims,
        private_key_pem,
        algorithm="RS256",
        headers={"kid": kid},
    )


@pytest.fixture(autouse=True)
def _reset_jwks_cache():
    fetch_jwks._cached_jwks = None
    fetch_jwks._fetched_at = 0.0
    yield
    fetch_jwks._cached_jwks = None
    fetch_jwks._fetched_at = 0.0


@pytest.fixture
def keys_and_pem():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-kid-1",
                "use": "sig",
                "alg": "RS256",
                "n": _b64url_uint(public_numbers.n),
                "e": _b64url_uint(public_numbers.e),
            }
        ]
    }
    return jwks, pem


@respx.mock
async def test_verify_clerk_jwt_happy_path(keys_and_pem, settings) -> None:
    jwks, pem = keys_and_pem
    respx.get(settings.clerk_jwks_url).mock(return_value=httpx.Response(200, json=jwks))
    claims_in = {
        "sub": "user_abc123",
        "iss": settings.clerk_issuer,
        "email": "tester@palkietalkie.test",
        "iat": int(time.time()),
        "exp": int(time.time()) + 600,
    }
    token = _sign(claims_in, pem)
    claims_out = await verify_clerk_jwt.verify_clerk_jwt(token)
    assert claims_out["sub"] == "user_abc123"
    assert claims_out["email"] == "tester@palkietalkie.test"


@respx.mock
async def test_verify_clerk_jwt_caches_jwks(keys_and_pem, settings) -> None:
    jwks, pem = keys_and_pem
    route = respx.get(settings.clerk_jwks_url).mock(
        return_value=httpx.Response(200, json=jwks)
    )
    token = _sign(
        {
            "sub": "u1",
            "iss": settings.clerk_issuer,
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        pem,
    )
    await verify_clerk_jwt.verify_clerk_jwt(token)
    await verify_clerk_jwt.verify_clerk_jwt(token)
    assert route.call_count == 1, "second verify should hit the in-process JWKS cache"


@respx.mock
async def test_verify_clerk_jwt_unknown_kid(keys_and_pem, settings) -> None:
    jwks, pem = keys_and_pem
    respx.get(settings.clerk_jwks_url).mock(return_value=httpx.Response(200, json=jwks))
    token = _sign(
        {
            "sub": "u1",
            "iss": settings.clerk_issuer,
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        pem,
        kid="not-in-jwks",
    )
    with pytest.raises(HTTPException) as exc:
        await verify_clerk_jwt.verify_clerk_jwt(token)
    assert exc.value.status_code == 401
    assert "kid" in exc.value.detail


@respx.mock
async def test_verify_clerk_jwt_bad_signature(keys_and_pem, settings) -> None:
    jwks, pem = keys_and_pem
    respx.get(settings.clerk_jwks_url).mock(return_value=httpx.Response(200, json=jwks))
    token = _sign(
        {
            "sub": "u1",
            "iss": settings.clerk_issuer,
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        pem,
    )
    tampered = token[:-2] + ("AA" if not token.endswith("AA") else "BB")
    with pytest.raises(HTTPException) as exc:
        await verify_clerk_jwt.verify_clerk_jwt(tampered)
    assert exc.value.status_code == 401


async def test_verify_clerk_jwt_malformed_header() -> None:
    with pytest.raises(HTTPException) as exc:
        await verify_clerk_jwt.verify_clerk_jwt("not-a-jwt")
    assert exc.value.status_code == 401


async def test_verify_clerk_jwt_no_kid(keys_and_pem, settings) -> None:
    _, pem = keys_and_pem
    raw = jwt.encode(
        {
            "sub": "u1",
            "iss": settings.clerk_issuer,
            "iat": int(time.time()),
            "exp": int(time.time()) + 600,
        },
        pem,
        algorithm="RS256",
    )
    with pytest.raises(HTTPException) as exc:
        await verify_clerk_jwt.verify_clerk_jwt(raw)
    assert exc.value.status_code == 401


async def test_resolve_current_user_creates_user_on_first_sight(
    monkeypatch, db
) -> None:
    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": "user_newcomer", "email": "new@palkietalkie.test"}

    monkeypatch.setattr(resolve_current_user, "verify_clerk_jwt", _fake_verify)

    user = await resolve_current_user.resolve_current_user(
        authorization="Bearer fake-token", db=db
    )
    assert user["clerk_user_id"] == "user_newcomer"
    assert user["email"] == "new@palkietalkie.test"


async def test_resolve_current_user_missing_bearer(db) -> None:
    with pytest.raises(HTTPException) as exc:
        await resolve_current_user.resolve_current_user(authorization=None, db=db)
    assert exc.value.status_code == 401


async def test_resolve_current_user_updates_email(monkeypatch, db) -> None:
    user_id = uuid.uuid4()
    clerk_id = "user_existing"
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, email) VALUES ($1, $2, $3)",
        user_id,
        clerk_id,
        "old@palkietalkie.test",
    )

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": "new@palkietalkie.test"}

    monkeypatch.setattr(resolve_current_user, "verify_clerk_jwt", _fake_verify)

    u = await resolve_current_user.resolve_current_user(authorization="Bearer t", db=db)
    assert u["email"] == "new@palkietalkie.test"
