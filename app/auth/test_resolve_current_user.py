"""Tests for resolve_current_user — JIT user-row creation + email refresh.

verify_clerk_jwt is monkeypatched so the test doesn't need a real JWKS; the focus here is the DB upsert behavior of the dependency itself."""

import asyncio
import inspect
import json
import uuid
from collections.abc import Iterator
from typing import Any

import asyncpg
import pytest
from fastapi import HTTPException

from app.auth import resolve_current_user as mod
from app.config import get_settings
from app.services.clerk.fetch_clerk_user import ClerkUserProfile
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.rows import UserRow


@pytest.fixture(autouse=True)
def disable_clerk_backfill(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Default every test here to no Clerk backend key, so resolve_current_user's Apple-backfill path stays inert and never fires a real api.clerk.com call (the local .env carries a real key). The backfill test opts in explicitly.
    monkeypatch.setenv("CLERK_SECRET_KEY", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_db_dependency_is_canonical_pooled_connection() -> None:
    # The db arg must default to the canonical pooled-connection dependency. The old get_db helper was renamed/removed; wiring anything else (or a stale import) would silently break connection lifecycle in prod.
    default = inspect.signature(mod.resolve_current_user).parameters["db"].default
    assert default.dependency is get_neon_connection


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
    # Locks the column rename: the SELECT/RETURNING projects users.preferred_name (formerly display_name); a stale name would KeyError in make_user_row. Unset on JIT creation.
    assert user["preferred_name"] is None
    # The SELECT must project correction_frequency (a missing projection would KeyError in make_user_row); a JIT user gets the column default.
    assert user["correction_frequency"] == "sometimes"
    persisted = await db.fetchval("SELECT COUNT(*) FROM users WHERE clerk_user_id = $1", clerk_id)
    assert persisted == 1


async def test_resolve_handles_concurrent_first_signin(
    monkeypatch: pytest.MonkeyPatch, db_url: str
) -> None:
    # On first sign-in the client fires authenticated requests on independent connections (RootView's GET /consent, and POST /devices/apns dispatched from its own Task in the APNs-token callback) that all SELECT-miss the not-yet-created user row and race to INSERT it. Without ON CONFLICT the losers raise UniqueViolationError on ix_users_clerk_user_id, surfacing as a 500 to the brand-new user (then "fixing itself" once the row exists). This locks the resolver idempotent under that race. Needs real concurrent connections, so it builds its own pool rather than using the single transaction-bound `db` fixture.
    clerk_id = f"user_race_{uuid.uuid4().hex[:8]}"

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": "race@example.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)

    async def _init(conn: asyncpg.Connection) -> None:
        await conn.set_type_codec(
            "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog"
        )

    n = 6
    pool = await asyncpg.create_pool(db_url, min_size=n, max_size=n, init=_init)
    try:

        async def _resolve_on_own_conn() -> UserRow:
            async with pool.acquire() as conn:
                return await mod.resolve_current_user(authorization="Bearer t", db=conn)

        results = await asyncio.gather(*(_resolve_on_own_conn() for _ in range(n)))
        persisted = await pool.fetchval(
            "SELECT COUNT(*) FROM users WHERE clerk_user_id = $1", clerk_id
        )
    finally:
        await pool.close()

    # Every concurrent request resolves to the SAME single row, none 500s, and exactly one row exists.
    assert {r["id"] for r in results} == {results[0]["id"]}
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


async def test_resolve_rejects_soft_deleted_account(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    # A soft-deleted account (deleted_at set) must be rejected on every request, even with a valid token — a re-login can't resurrect access. The row stays for counts.
    clerk_id = f"user_deleted_{uuid.uuid4().hex[:8]}"
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, email, deleted_at) VALUES ($1, $2, $3, NOW())",
        uuid.uuid4(),
        clerk_id,
        "gone@example.test",
    )

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id, "email": "gone@example.test"}

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    with pytest.raises(HTTPException) as exc:
        await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert exc.value.status_code == 403


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


async def test_resolve_backfills_email_and_first_name_from_clerk_when_jwt_omits_them(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    # Apple sign-in: the session JWT carries only `sub`, so the JIT row is created with NULL email + preferred_name. The resolver backfills both from Clerk's Backend API so the user has a real label (tutor address + Slack) instead of a raw clerk id. preferred_name is the FIRST name only.
    clerk_id = f"user_apple_{uuid.uuid4().hex[:8]}"

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id}

    async def _fake_fetch(_cid: str, _secret: str) -> ClerkUserProfile:
        return ClerkUserProfile(email="relay@privaterelay.appleid.com", first_name="Taka")

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    monkeypatch.setattr(mod, "fetch_clerk_user", _fake_fetch)
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_x")
    get_settings.cache_clear()

    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert user["email"] == "relay@privaterelay.appleid.com"
    assert user["preferred_name"] == "Taka"
    row = await db.fetchrow(
        "SELECT email, preferred_name FROM users WHERE clerk_user_id = $1", clerk_id
    )
    assert row is not None
    assert row["email"] == "relay@privaterelay.appleid.com"
    assert row["preferred_name"] == "Taka"


async def test_resolve_skips_clerk_backfill_when_no_secret_configured(
    monkeypatch: pytest.MonkeyPatch, db: DBConn
) -> None:
    # Without a Clerk backend key (local/test default), the resolver must NOT call Clerk — otherwise every authenticated request with a not-yet-named row would hit the network. The autouse fixture already empties the key.
    clerk_id = f"user_nosecret_{uuid.uuid4().hex[:8]}"
    called = False

    async def _fake_verify(token: str) -> dict[str, Any]:
        return {"sub": clerk_id}

    async def _fake_fetch(_cid: str, _secret: str) -> ClerkUserProfile | None:
        nonlocal called
        called = True
        return None

    monkeypatch.setattr(mod, "verify_clerk_jwt", _fake_verify)
    monkeypatch.setattr(mod, "fetch_clerk_user", _fake_fetch)

    user = await mod.resolve_current_user(authorization="Bearer t", db=db)
    assert not called, "no Clerk secret → no Clerk call"
    assert user["preferred_name"] is None
