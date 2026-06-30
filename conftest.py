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
import platform
import shutil
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import asyncpg
import pytest
from httpx import AsyncClient
from testcontainers.postgres import PostgresContainer

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow

if TYPE_CHECKING:
    from app.config import Settings


def _load_backend_dotenv() -> None:
    # Auto-load backend/.env so sandbox tests can read real credentials without manual `set -a; source .env`. setdefault keeps shell/CI env winning if already exported. Single-line values only — anything PEM-shaped lives as a file under backend/secrets/ and is loaded separately below.
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if value.startswith(('"', "'")) and value.endswith(value[0]) and len(value) >= 2:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _load_pem_secrets() -> None:
    # PEM-formatted credentials live as files under backend/secrets/ rather than in .env (env vars are conventionally single-line). Map each known filename to the env var the test code reads. CI sets the env var directly via GH Secrets and skips this loader.
    secrets_dir = Path(__file__).parent / "secrets"
    if not secrets_dir.exists():
        return
    pem_files = {
        "apple_storekit_api.p8": "APPLE_STOREKIT_PRIVATE_KEY",
        "apple_asc_api.p8": "APPLE_ASC_PRIVATE_KEY",
    }
    for filename, env_var in pem_files.items():
        path = secrets_dir / filename
        if path.exists():
            os.environ.setdefault(env_var, path.read_text())


_load_backend_dotenv()
_load_pem_secrets()

# Stash the real Neon URL (from .env / GH Secret) BEFORE the testcontainer fixture overwrites NEON_DATABASE_URL with a local Postgres container. Sandbox tests read this so they hit dev Neon (where the deployed dev backend writes) instead of the per-session container (which the backend can't see).
os.environ.setdefault("DEV_NEON_DATABASE_URL", os.environ.get("NEON_DATABASE_URL", ""))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("CLERK_JWKS_URL", "https://test.clerk.test/.well-known/jwks.json")
os.environ.setdefault("CLERK_ISSUER", "https://test.clerk.test")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "whsec_test_secret")
os.environ.setdefault("STRIPE_SECRET_KEY", "sk_test_dummy")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")
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


_PROVIDER_APPS = ("Docker", "OrbStack", "Rancher Desktop")
_PROVIDER_BINS = ("colima",)


def _docker_running() -> bool:
    docker = shutil.which("docker")
    if docker is None:
        return False
    return subprocess.run([docker, "info"], capture_output=True, check=False).returncode == 0  # noqa: S603 — path from shutil.which


def _install_docker_desktop() -> None:
    """Install Docker Desktop via Homebrew cask. Only called when no docker provider is present on this host."""
    if platform.system() != "Darwin":
        raise RuntimeError(
            "Auto-install only supported on macOS; install docker manually on this OS."
        )
    brew = shutil.which("brew")
    if brew is None:
        raise RuntimeError(
            "No docker provider installed and `brew` isn't on PATH — install Homebrew first."
        )
    print("[conftest] no docker provider found, installing Docker Desktop via Homebrew cask…")
    subprocess.run([brew, "install", "--cask", "docker"], check=True)  # noqa: S603 — path from shutil.which


def _start_daemon() -> str | None:
    """Boot whichever docker provider is installed on this host. Returns the provider name we launched (so we can quit it on teardown) or None if we couldn't auto-start."""
    if platform.system() == "Darwin":
        for app_name in _PROVIDER_APPS:
            if Path(f"/Applications/{app_name}.app").is_dir():
                open_bin = shutil.which("open")
                if open_bin is None:
                    return None
                subprocess.run([open_bin, "-a", app_name], check=True)  # noqa: S603 — path from shutil.which
                return app_name
    for bin_name in _PROVIDER_BINS:
        bin_path = shutil.which(bin_name)
        if bin_path is not None:
            subprocess.run([bin_path, "start"], check=True)  # noqa: S603 — path from shutil.which
            return bin_name
    return None


def _stop_daemon(provider: str) -> None:
    if provider in _PROVIDER_APPS:
        osascript = shutil.which("osascript")
        if osascript is None:
            return
        subprocess.run([osascript, "-e", f'quit app "{provider}"'], check=False)  # noqa: S603 — path from shutil.which
        return
    bin_path = shutil.which(provider)
    if bin_path is not None:
        subprocess.run([bin_path, "stop"], check=False)  # noqa: S603 — path from shutil.which


def _ensure_docker_daemon() -> str | None:
    """testcontainers needs a live docker daemon. Boot whichever provider is installed; install Docker Desktop via Homebrew if none is present. Returns the provider name iff we were the ones who started it (so we can stop it on teardown)."""
    if _docker_running():
        return None
    provider = _start_daemon()
    if provider is None:
        _install_docker_desktop()
        provider = _start_daemon()
    if provider is None:
        raise RuntimeError("Docker provider install completed but no provider was detected after.")
    deadline = time.monotonic() + 90.0
    while not _docker_running():
        if time.monotonic() > deadline:
            raise RuntimeError(f"{provider} didn't come up within 90s — check the menubar / shell.")
        time.sleep(2)
    return provider


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
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    """Session-scoped loop so the per-test asyncio fixtures share a loop with the container setup."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def db_url() -> Iterator[str]:
    """One Postgres container for the whole pytest session, migrations applied once."""
    started_provider = _ensure_docker_daemon()
    try:
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
    finally:
        if started_provider is not None:
            _stop_daemon(started_provider)


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
async def fake_user(db: DBConn) -> UserRow:
    """Baseline user row for router tests. created_at is set well in the past so the baseline is an ESTABLISHED free user, past the first-month trial — otherwise every free-cap test would see a trial user with no caps. Trial behavior is covered by tests that set created_at explicitly recent."""
    user_id = uuid.uuid4()
    now = datetime.now(UTC)
    established = now - timedelta(days=60)
    row = await db.fetchrow(
        """INSERT INTO users (id, clerk_user_id, email, preferred_name, native_languages,
                              location_city, timezone, created_at, updated_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
           RETURNING id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                     preferred_name, name_pronunciation, native_languages, target_language, target_accents,
                     proficiency, tutor_speaking_speed, goals,
                     location_city, timezone,
                     personalization_consent, product_improvement_consent, consent_screen_seen_at, deleted_at""",
        user_id,
        f"user_{uuid.uuid4().hex[:12]}",
        "testuser@palkietalkie.test",
        "Test User",
        ["Japanese"],
        "Tokyo",
        "Asia/Tokyo",
        established,
        now,
    )
    assert row is not None
    # asyncpg.Record indexes as Any → assignable to the TypedDict's declared field types.
    # rows.py is auto-generated from the live Neon schema, so the column set is guaranteed to match.
    return UserRow(
        id=row["id"],
        clerk_user_id=row["clerk_user_id"],
        email=row["email"],
        premium=row["premium"],
        premium_ends_at=row["premium_ends_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        preferred_name=row["preferred_name"],
        name_pronunciation=row["name_pronunciation"],
        native_languages=list(row["native_languages"]),
        target_language=row["target_language"],
        target_accents=list(row["target_accents"]),
        proficiency=row["proficiency"],
        tutor_speaking_speed=row["tutor_speaking_speed"],
        goals=row["goals"],
        location_city=row["location_city"],
        timezone=row["timezone"],
        personalization_consent=row["personalization_consent"],
        product_improvement_consent=row["product_improvement_consent"],
        consent_screen_seen_at=row["consent_screen_seen_at"],
        deleted_at=row["deleted_at"],
    )


@pytest.fixture
async def app_with_overrides(
    db: DBConn, fake_user: UserRow
) -> AsyncIterator[tuple[AsyncClient, UserRow]]:
    """Async test client with auth + DB dependency overrides applied.

    - ``current_user`` is replaced with a no-op that returns ``fake_user``.
    - ``get_neon_connection`` yields the per-test transaction-bound connection so router writes and test
      assertions share the same view.
    """
    from httpx import ASGITransport, AsyncClient

    from app.auth.resolve_current_user import resolve_current_user
    from app.main import create_app
    from app.services.neon.get_neon_connection import get_neon_connection

    async def _override_get_db() -> AsyncIterator[DBConn]:
        yield db

    async def _override_current_user() -> UserRow:
        """Re-read the fake user on the per-request connection so route mutations are visible."""
        row = await db.fetchrow(
            """SELECT id, clerk_user_id, email, premium, premium_ends_at, created_at, updated_at,
                      preferred_name, name_pronunciation, native_languages, target_language, target_accents,
                      proficiency, tutor_speaking_speed, goals,
                      location_city, timezone,
                      personalization_consent, product_improvement_consent, consent_screen_seen_at, deleted_at
               FROM users
               WHERE id = $1""",
            fake_user["id"],
        )
        assert row is not None
        return UserRow(
            id=row["id"],
            clerk_user_id=row["clerk_user_id"],
            email=row["email"],
            premium=row["premium"],
            premium_ends_at=row["premium_ends_at"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            preferred_name=row["preferred_name"],
            name_pronunciation=row["name_pronunciation"],
            native_languages=list(row["native_languages"]),
            target_language=row["target_language"],
            target_accents=list(row["target_accents"]),
            proficiency=row["proficiency"],
            tutor_speaking_speed=row["tutor_speaking_speed"],
            goals=row["goals"],
            location_city=row["location_city"],
            timezone=row["timezone"],
            personalization_consent=row["personalization_consent"],
            product_improvement_consent=row["product_improvement_consent"],
            consent_screen_seen_at=row["consent_screen_seen_at"],
            deleted_at=row["deleted_at"],
        )

    fastapi_app = create_app()
    fastapi_app.dependency_overrides[resolve_current_user] = _override_current_user
    fastapi_app.dependency_overrides[get_neon_connection] = _override_get_db
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac, fake_user
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
async def client(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> AsyncIterator[AsyncClient]:
    cl, _ = app_with_overrides
    yield cl


@pytest.fixture
def settings() -> Iterator[Settings]:
    """Fresh ``Settings`` snapshot for tests that read config directly."""
    from app.config import get_settings

    get_settings.cache_clear()
    s = get_settings()
    yield s
    get_settings.cache_clear()
