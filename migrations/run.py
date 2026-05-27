"""Apply unapplied .sql files in this directory, in lexical order."""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg


def _normalize(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def _run() -> None:
    url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("NEON_DATABASE_URL is required")
    conn = await asyncpg.connect(_normalize(url))
    try:
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_version ("
            " version TEXT PRIMARY KEY,"
            " applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
            ")"
        )
        applied = {
            row[0] for row in await conn.fetch("SELECT version FROM schema_version")
        }
        files = sorted(
            Path(__file__).resolve().parent.glob("*.sql")
        )  # noqa: ASYNC240 — sync glob is fine at migration time
        for path in files:
            version = path.stem
            if version in applied:
                continue
            print(f"applying {version}", flush=True)
            async with conn.transaction():
                await conn.execute(path.read_text())
                await conn.execute(
                    "INSERT INTO schema_version (version) VALUES ($1)",
                    version,
                )
        print("migrations: ok", flush=True)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(_run())
