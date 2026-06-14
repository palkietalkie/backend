import os
from pathlib import Path

# scripts/read_env_value.py → parents[1] is the backend/ root that holds .env.
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"


def read_env_value(key: str) -> str | None:
    """Return one env var's value, preferring the shell env and falling back to backend/.env.

    `uv run` and git hooks don't load .env, so a script reading only os.environ silently misses local config — that's how the schema-type generator kept skipping in pre-commit and let rows.py drift uncaught.
    """
    value = os.environ.get(key)
    if value:
        return value
    if not _ENV_PATH.exists():
        return None
    prefix = f"{key}="
    for line in _ENV_PATH.read_text().splitlines():
        if line.startswith(prefix):
            return line[len(prefix) :].strip().strip('"').strip("'")
    return None
