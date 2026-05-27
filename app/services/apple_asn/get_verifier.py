from typing import Any

from app.config import get_settings
from app.services.apple_asn import _state
from app.services.apple_asn._sdk import (
    APPLE_LIB_AVAILABLE,
    AppleEnv,
    SignedDataVerifier,
)
from app.services.apple_asn.exceptions import AppleLibraryMissingError
from app.services.apple_asn.load_apple_root_certs import load_apple_root_certs


async def get_verifier() -> Any:
    # Construction is cheap but the root-cert fetch is not — so lock and cache.
    if not APPLE_LIB_AVAILABLE:
        raise AppleLibraryMissingError(
            "app-store-server-library not installed — cannot verify Apple ASN payloads. "
            "Install it with `pip install app-store-server-library` and redeploy."
        )
    if _state.VERIFIER_CACHE is not None:
        return _state.VERIFIER_CACHE
    async with _state.VERIFIER_LOCK:
        if _state.VERIFIER_CACHE is not None:
            return _state.VERIFIER_CACHE
        settings = get_settings()
        roots = await load_apple_root_certs()
        env = (
            AppleEnv.SANDBOX
            if settings.app_env != "production"
            else AppleEnv.PRODUCTION
        )
        # OCSP/CRL would slow every webhook by 100ms+, so disable online checks.
        _state.VERIFIER_CACHE = SignedDataVerifier(
            root_certificates=roots,
            enable_online_checks=False,
            environment=env,
            bundle_id=settings.apple_bundle_id,
        )
        return _state.VERIFIER_CACHE
