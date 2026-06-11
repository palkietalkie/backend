"""Structural type for the Apple JWS verifier.

Satisfied by the SDK's SignedDataVerifier (production) and FakeVerifier (tests) without either inheriting from it. Methods return `object` because every caller immediately runs the result through coerce_to_dict / getattr — the SDK's concrete attrs-payload types are never used statically.
"""

from typing import Protocol


class VerifierProtocol(Protocol):
    # Params are positional-only (/) so any implementation (the SDK, FakeVerifier) conforms regardless of how it names them — these methods are only ever called positionally.
    def verify_and_decode_notification(self, signed_payload: str, /) -> object: ...
    def verify_and_decode_signed_transaction(self, signed_transaction: str, /) -> object: ...
    def verify_and_decode_renewal_info(self, signed_renewal: str, /) -> object: ...
