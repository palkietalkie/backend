"""Module-level caches shared by load_apple_root_certs.py / get_verifier.py / reset_caches.py."""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.apple_asn._sdk import SignedDataVerifier

ROOT_CERTS_CACHE: list[bytes] | None = None
VERIFIER_CACHE: SignedDataVerifier | None = None
VERIFIER_LOCK = asyncio.Lock()
