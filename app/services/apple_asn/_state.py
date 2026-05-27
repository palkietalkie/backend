"""Module-level caches shared by load_apple_root_certs.py / get_verifier.py / reset_caches.py."""

import asyncio
from typing import Any

ROOT_CERTS_CACHE: list[bytes] | None = None
VERIFIER_CACHE: Any = None
VERIFIER_LOCK = asyncio.Lock()
