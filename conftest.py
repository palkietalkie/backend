"""Shared pytest fixtures.

A real Postgres is spun up via testcontainers once per session, and the
``migrations/*.sql`` files are applied against it. Each test runs inside a
SAVEPOINT-backed transaction that rolls back at teardown so rows from one test
don't bleed into the next.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import asyncpg
import pytest
from testcontainers.postgres import PostgresContainer

if TYPE_CHECKING:
    from app.services.neon.db_conn import DBConn

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("CLERK_JWKS_URL", "https://test.clerk.test/.well-known/jwks.json")
os.environ.setdefault("CLERK_ISSUER", "https://test.clerk.test")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
os.environ.setdefault("APPLE_BUNDLE_ID", "ai.palkietalkie.test")
os.environ.setdefault("PERSONAPLEX_HOST", "personaplex.test")
os.environ.setdefault("PERSONAPLEX_PORT", "443")
os.environ.setdefault("PERSONAPLEX_SCHEME", "wss")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_ID", "test-google-client-id")
os.environ.setdefault("GOOGLE_OAUTH_CLIENT_SECRET", "test-google-client-secret")
os.environ.setdefault("NEO4J_URI", "bolt://localhost:7687")
os.environ.setdefault("WS_TICKET_SECRET", "test-ws-ticket-secret")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-openai-key")
os.environ.setdefault("INFERENCE_PROVIDER", "personaplex")

_MIGRATIONS_DIR = Path(__file__).parent / "migrations"


async def _init_connection(conn: DBConn) -> None:
    await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
    await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")


async def _apply_migrations(url: str) -> None:
    conn = await asyncpg.connect(url)
    try:
        for path in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            await conn.execute(path.read_text())
    finally:
        await conn.close()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop() -> Iterator:
    """Session-scoped loop so the per-test asyncio fixtures share a loop with the container setup."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_url() -> Iterator[str]:
    """One Postgres container for the whole pytest session, migrations applied once."""
    with PostgresContainer("postgres:16-alpine") as pg:
        raw = pg.get_connection_url()
        url = raw.replace("postgresql+psycopg2://", "postgresql://")
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_apply_migrations(url))
        finally:
            loop.close()
        os.environ["NEON_DATABASE_URL"] = url
        from app.config import get_settings

        get_settings.cache_clear()
        get_settings()
        yield url


@pytest.fixture
async def pool(db_url: str) -> AsyncIterator[asyncpg.Pool]:
    """One pool per test so each connection lives on the test's event loop."""
    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=4, init=_init_connection)
    try:
        yield pool
    finally:
        await pool.close()


@pytest.fixture
async def db(pool: asyncpg.Pool) -> AsyncIterator[DBConn]:
    """Per-test connection wrapped in a transaction that rolls back at teardown.

    Tests can both seed rows AND assert against them on the same connection without leaking
    state to other tests.
    """
    async with pool.acquire() as conn:
        tx = conn.transaction()
        await tx.start()
        try:
            yield conn
        finally:
            await tx.rollback()


@pytest.fixture
async def fake_user(db: DBConn) -> dict:
    """Baseline user row for router tests."""
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    row = await db.fetchrow(
        """INSERT INTO users (id, clerk_user_id, email, display_name, native_language,
                              location_city, timezone, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8)
           RETURNING id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                     display_name, native_language, target_accent, goals,
                     location_city, timezone,
                     personalization_consent, product_improvement_consent, consent_screen_seen_at""",
        user_id,
        f"user_{uuid.uuid4().hex[:12]}",
        "testuser@palkietalkie.test",
        "Test User",
        "ja",
        "Tokyo",
        "Asia/Tokyo",
        now,
    )
    assert row is not None
    return dict(row)


@pytest.fixture
async def app_with_overrides(db: DBConn, fake_user: dict):
    """Async test client with auth + DB dependency overrides applied.

    - ``current_user`` is replaced with a no-op that returns ``fake_user``.
    - ``get_db`` yields the per-test transaction-bound connection so router writes and test
      assertions share the same view.
    """
    from httpx import ASGITransport, AsyncClient

    from app.auth.resolve_current_user import resolve_current_user
    from app.main import create_app
    from app.services.neon.get_db import get_db

    async def _override_get_db() -> AsyncIterator[DBConn]:
        yield db

    async def _override_current_user() -> dict:
        """Re-read the fake user on the per-request connection so route mutations are visible."""
        row = await db.fetchrow(
            """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                      display_name, native_language, target_accent, goals,
                      location_city, timezone,
                      personalization_consent, product_improvement_consent, consent_screen_seen_at
               FROM users
               WHERE id = $1""",
            fake_user["id"],
        )
        assert row is not None
        return dict(row)

    fastapi_app = create_app()
    fastapi_app.dependency_overrides[resolve_current_user] = _override_current_user
    fastapi_app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac, fake_user
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def client(app_with_overrides) -> AsyncIterator:
    cl, _ = app_with_overrides
    yield cl


@pytest.fixture
def settings() -> Iterator:
    """Fresh ``Settings`` snapshot for tests that read config directly."""
    from app.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    yield s
    get_settings.cache_clear()
