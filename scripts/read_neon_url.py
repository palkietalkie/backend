import re
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]


def read_neon_url(env: str) -> str:
    """Return the NEON_DATABASE_URL for a specific environment ("dev" → backend/.env, "prd" → backend/.env.production).

    Deliberately file-specific and NOT shell-first (unlike read_env_value): a cross-database tool must read each environment's URL from its own file, or a NEON_DATABASE_URL exported in the shell would silently stand in for both and point dev and prd at the same database.
    """
    env_file = _BACKEND / (".env.production" if env == "prd" else ".env")
    m = re.search(r"^NEON_DATABASE_URL=(.+)$", env_file.read_text(), re.MULTILINE)
    if not m:
        raise SystemExit(f"NEON_DATABASE_URL not found in {env_file}")
    return m.group(1).strip().strip('"').strip("'")
