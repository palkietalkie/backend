import os
import sys


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        sys.exit(f"FAIL: env {name} is required.")
    return v
