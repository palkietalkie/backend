"""SDK availability shim. Kept private to the apple_asn package."""

from typing import Any

# pyright: reportAssignmentType=false
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
    AppleEnv = None  # type: ignore[assignment,misc]
    SignedDataVerifier = None  # type: ignore[assignment,misc]

    class VerificationException(Exception):  # type: ignore[no-redef,assignment]
        pass


_ = Any  # keep typing import live for downstream re-export consumers
