"""Local stub for the stripe Python SDK 22.x — covers only the surface this codebase touches.

The upstream SDK ships untyped `payload, sig_header, secret` kwargs on ``Webhook.construct_event`` and similar functions, which pyright surfaces as ``Unknown``. We model just the call sites we use; extend on demand.
"""

api_key: str | None

class SignatureVerificationError(Exception):
    pass

class Event:
    object: str | None
    type: str

    def to_dict(self) -> dict[str, object]: ...

class Webhook:
    DEFAULT_TOLERANCE: int

    @staticmethod
    def construct_event(
        payload: bytes | str,
        sig_header: str,
        secret: str,
        tolerance: int = ...,
        api_key: str | None = ...,
    ) -> Event: ...
