import sys

import asyncpg

from app.services.neon.normalize_neon_url import normalize_neon_url
from scripts.read_env_value import read_env_value

SKIP_TABLES: frozenset[str] = frozenset({"schema_version"})


async def fetch_schema() -> dict[str, list[tuple[str, str, str, bool]]]:
    """Return `{table_name: [(column, pg_type, udt_name, nullable), ...]}` from `information_schema`.

    Reads NEON_DATABASE_URL (shell env, then backend/.env via read_env_value). Exits 0 (not 1) when absent — a fresh machine with no .env can't reach the DB and shouldn't be blocked from committing before setup.

    Columns come back in `ordinal_position` order so the generated TypedDict matches the table's physical column order — keeps the emitted file diff-friendly.
    """
    url = read_env_value("NEON_DATABASE_URL")
    if not url:
        print(
            "generate_neon_types: NEON_DATABASE_URL not in env or backend/.env — skipping",
            file=sys.stderr,
        )
        sys.exit(0)
    conn = await asyncpg.connect(normalize_neon_url(url))
    try:
        rows = await conn.fetch(
            """
            SELECT c.table_name, c.column_name, c.data_type, c.udt_name, c.is_nullable, c.ordinal_position
            FROM information_schema.columns c
            JOIN information_schema.tables t
              ON t.table_schema = c.table_schema AND t.table_name = c.table_name
            WHERE c.table_schema = 'public'
              AND t.table_type = 'BASE TABLE'
            ORDER BY c.table_name, c.ordinal_position
            """
        )
    finally:
        await conn.close()
    schema: dict[str, list[tuple[str, str, str, bool]]] = {}
    for r in rows:
        table = r["table_name"]
        if table in SKIP_TABLES:
            continue
        schema.setdefault(table, []).append(
            (r["column_name"], r["data_type"], r["udt_name"], r["is_nullable"] == "YES")
        )
    return schema
