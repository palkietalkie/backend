# /// script
# requires-python = ">=3.14"
# dependencies = ["asyncpg>=0.29"]
# ///
"""Generate `app/services/neon/rows.py` from the live Neon dev schema.

Reads ``NEON_DATABASE_URL_DEV`` (or ``NEON_DATABASE_URL`` as a fallback), introspects
``information_schema.columns`` for every user-defined table, and emits one TypedDict per table.

Run via pre-commit (see ``scripts/git/pre-commit``) — if the generator's output differs from the
committed ``rows.py``, the hook fails and asks the dev to re-stage.

Manual usage:

    uv run scripts/generate_neon_types.py

Naming: snake_case table name → PascalCase + "Row" (``users`` → ``UserRow``,
``persona_likes`` → ``PersonaLikeRow``). Plural tables get singularized when possible
(``users`` → ``User``, but ``mistakes`` → ``Mistake``).
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import asyncpg

OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "services" / "neon" / "rows.py"

# Skip these — internal / not part of the app's typed surface.
SKIP_TABLES: frozenset[str] = frozenset({"schema_version"})

PG_TO_PYTHON: dict[str, str] = {
    "uuid": "uuid.UUID",
    "text": "str",
    "character varying": "str",
    "varchar": "str",
    "char": "str",
    "boolean": "bool",
    "bool": "bool",
    "smallint": "int",
    "integer": "int",
    "bigint": "int",
    "real": "float",
    "double precision": "float",
    "numeric": "float",
    "timestamp without time zone": "datetime",
    "timestamp with time zone": "datetime",
    "timestamptz": "datetime",
    "date": "date",
    "time without time zone": "time",
    "time with time zone": "time",
    "json": "dict[str, Any]",
    "jsonb": "dict[str, Any]",
    "bytea": "bytes",
    # Postgres ENUMs surface as "USER-DEFINED" via information_schema.data_type. asyncpg returns them as plain strings, so the Python type is str.
    "USER-DEFINED": "str",
}


def singularize(name: str) -> str:
    # Crude but enough for our schema. Override with explicit irregulars if we hit one.
    if name.endswith("ies"):
        return name[:-3] + "y"
    if name.endswith("ses") or name.endswith("xes") or name.endswith("zes"):
        return name[:-2]
    if name.endswith("s"):
        return name[:-1]
    return name


def table_to_class_name(table: str) -> str:
    base = singularize(table)
    parts = re.split(r"_+", base)
    return "".join(p.capitalize() for p in parts if p) + "Row"


def normalize_url(url: str) -> str:
    # Strip SQLAlchemy "+asyncpg" suffix and psycopg2-only query params asyncpg doesn't understand.
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://") :]
    parts = urlsplit(url)
    if parts.query:
        kept = [
            kv
            for kv in parts.query.split("&")
            if not kv.startswith(("sslmode=", "channel_binding="))
        ]
        url = urlunsplit(parts._replace(query="&".join(kept)))
    return url


async def fetch_schema() -> dict[str, list[tuple[str, str, bool]]]:
    # Returns {table_name: [(column_name, pg_type, nullable), ...]} in column-position order.
    url = os.environ.get("NEON_DATABASE_URL_DEV") or os.environ.get("NEON_DATABASE_URL")
    if not url:
        print(
            "generate_neon_types: NEON_DATABASE_URL_DEV (or NEON_DATABASE_URL) not set — skipping",
            file=sys.stderr,
        )
        sys.exit(0)
    conn = await asyncpg.connect(normalize_url(url))
    try:
        rows = await conn.fetch(
            """
            SELECT c.table_name, c.column_name, c.data_type, c.is_nullable, c.ordinal_position
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
    schema: dict[str, list[tuple[str, str, bool]]] = {}
    for r in rows:
        table = r["table_name"]
        if table in SKIP_TABLES:
            continue
        schema.setdefault(table, []).append(
            (r["column_name"], r["data_type"], r["is_nullable"] == "YES")
        )
    return schema


def render(schema: dict[str, list[tuple[str, str, bool]]]) -> str:
    needs_uuid = False
    needs_datetime = False
    needs_date = False
    needs_time = False
    needs_any = False

    for cols in schema.values():
        for _name, pg_type, _nullable in cols:
            py = PG_TO_PYTHON.get(pg_type, "Any")
            if py == "uuid.UUID":
                needs_uuid = True
            elif py == "datetime":
                needs_datetime = True
            elif py == "date":
                needs_date = True
            elif py == "time":
                needs_time = True
            elif py == "dict[str, Any]" or py == "Any":
                needs_any = True

    lines: list[str] = [
        '"""TypedDicts mirroring the live Neon schema.',
        "",
        "Generated by ``scripts/generate_neon_types.py`` — do not hand-edit.",
        "The pre-commit hook re-runs the generator and fails the commit if this file drifts.",
        '"""',
        "",
    ]
    if needs_uuid:
        lines.append("import uuid")
    datetime_imports: list[str] = []
    if needs_datetime:
        datetime_imports.append("datetime")
    if needs_date:
        datetime_imports.append("date")
    if needs_time:
        datetime_imports.append("time")
    if datetime_imports:
        lines.append(f"from datetime import {', '.join(datetime_imports)}")
    typing_imports = ["TypedDict"]
    if needs_any:
        typing_imports.insert(0, "Any")
    lines.append(f"from typing import {', '.join(typing_imports)}")
    lines.append("")

    for table in sorted(schema):
        cols = schema[table]
        class_name = table_to_class_name(table)
        lines.append("")
        lines.append(f"class {class_name}(TypedDict):")
        for col_name, pg_type, nullable in cols:
            py = PG_TO_PYTHON.get(pg_type, "Any")
            if nullable:
                py = f"{py} | None"
            lines.append(f"    {col_name}: {py}")
    lines.append("")
    return "\n".join(lines)


async def main() -> int:
    schema = await fetch_schema()
    if not schema:
        print("generate_neon_types: no tables found in 'public' schema", file=sys.stderr)
        return 1
    text = render(schema)
    OUT_PATH.write_text(text)
    print(
        f"generate_neon_types: wrote {OUT_PATH.relative_to(OUT_PATH.parents[3])} "
        f"({len(schema)} tables)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
