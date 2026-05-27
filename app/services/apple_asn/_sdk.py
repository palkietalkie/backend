"""SDK availability shim. Kept private to the apple_asn package."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Pyright gets the SDK-typed names directly; runtime falls through to the try/except below.
    from appstoreserverlibrary.models.Environment import Environment as AppleEnv
    from appstoreserverlibrary.signed_data_verifier import (
        SignedDataVerifier,
        VerificationException,
    )

    APPLE_LIB_AVAILABLE = True
else:
    try:
        from appstoreserverlibrary.models.Environment import (
            Environment as AppleEnv,
        )
        from appstoreserverlibrary.signed_data_verifier import (
            SignedDataVerifier,
            VerificationException,
        )

        APPLE_LIB_AVAILABLE = True
    except ImportError:  # pragma: no cover — handled gracefully at runtime
        APPLE_LIB_AVAILABLE = False
        AppleEnv = None
        SignedDataVerifier = None

        class VerificationException(Exception):
            pass


__all__ = [
    "APPLE_LIB_AVAILABLE",
    "AppleEnv",
    "SignedDataVerifier",
    "VerificationException",
]
