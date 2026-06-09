"""Tests for resolve_current_user — JIT user-row creation + email refresh.

verify_clerk_jwt is monkeypatched so the test doesn't need a real JWKS; the focus here is the DB upsert behavior of the dependency itself."""

import uuid
from typing import Any

import pytest
from fastapi import HTTPException

from app.auth import resolve_current_user as mod
from app.services.neon.db_conn import DBConn


async def test_resolve_creates_user_when_missing(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    clerk_id = f"user_jit_{uuid.uuid4().hex[:8]}"

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": "jit@palkietalkie.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert user["clerk_user_id"] == clerk_id
    assert user["email"] == "jit@palkietalkie.test"
    persisted = await db.fetchval("SELECT COUNT(*) FROM users WHERE clerk_user_id = $1", clerk_id)
    assert persisted == 1


async def test_resolve_updates_email_when_changed(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    clerk_id = f"user_email_{uuid.uuid4().hex[:8]}"
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, email) VALUES ($1, $2, $3)",
        user_id,
        clerk_id,
        "old@example.test",
    )

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": "new@example.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert user["email"] == "new@example.test"
    persisted = await db.fetchval("SELECT email FROM users WHERE id = $1", user_id)
    assert persisted == "new@example.test"


async def test_resolve_keeps_email_when_token_omits_it(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    clerk_id = f"user_no_email_{uuid.uuid4().hex[:8]}"
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, email) VALUES ($1, $2, $3)",
        user_id,
        clerk_id,
        "keep@example.test",
    )

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert user["email"] == "keep@example.test"


async def test_resolve_rejects_token_without_sub(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"email": "no-sub@example.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    with pytest.raises(HTTPException) as exc:
        await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert exc.value.status_code == 401


async def test_resolve_missing_authorization_header(db: DBConn) -> None:
    with pytest.raises(HTTPException) as exc:
        await mod.resolve_current_user(authorization=None, db=db)
    assert exc.value.status_code == 401


async def test_resolve_accepts_primary_email_address_claim(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    # Some Clerk templates put the email under a different claim name; the resolver tolerates both.
    clerk_id = f"user_pri_{uuid.uuid4().hex[:8]}"

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "primary_email_address": "pri@example.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert user["email"] == "pri@example.test"
