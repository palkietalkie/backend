# /// script
# requires-python = ">=3.14"
# dependencies = ["asyncpg>=0.29"]
# ///
"""Generate `app/services/neon/rows.py` from the live Neon dev schema.

Orchestrator only — fetches the schema via `fetch_schema`, renders via `render_rows`, writes the result. Reads `NEON_DATABASE_URL` (shell env, then backend/.env). Run via pre-commit hook (see `scripts/git/pre-commit`) so any schema change forces a regen.

Manual usage:

cd backend && uv run scripts/neon/generate_neon_types.py"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.neon.fetch_schema import fetch_schema  # noqa: E402
from scripts.neon.render_rows import render_rows  # noqa: E402

OUT_PATH = Path(__file__).resolve().parents[2] / "app" / "services" / "neon" / "rows.py"


async def main() -> int:
    schema = await fetch_schema()
    if not schema:
        print("generate_neon_types: no tables found in 'public' schema", file=sys.stderr)
        return 1
    text = render_rows(schema)
    OUT_PATH.write_text(text)
    print(
        f"generate_neon_types: wrote {OUT_PATH.relative_to(OUT_PATH.parents[3])} "
        f"({len(schema)} tables)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
