"""Shared FakeVerifier + helpers for per-function apple_asn tests."""

from typing import Any

from app.services.apple_asn._sdk import VerificationException


def make_verification_error(msg: str) -> Exception:
    exc = VerificationException.__new__(VerificationException)
    exc.args = (msg,)
    return exc


class FakeVerifier:
    """Mimics SignedDataVerifier. Routes signed payloads back through plain dicts."""

    def __init__(
        self,
        *,
        notification: Any,
        transaction: dict[str, Any] | None = None,
        renewal: dict[str, Any] | None = None,
        outer_fail: bool = False,
        inner_fail: bool = False,
    ) -> None:
        self._notification = notification
        self._transaction: dict[str, Any] = transaction or {}
        self._renewal: dict[str, Any] = renewal or {}
        self._outer_fail = outer_fail
        self._inner_fail = inner_fail

    def verify_and_decode_notification(self, _payload: str) -> Any:
        if self._outer_fail:
            raise make_verification_error("bad outer sig")
        return self._notification

    def verify_and_decode_signed_transaction(self, _payload: str) -> dict[str, Any]:
        if self._inner_fail:
            raise make_verification_error("bad inner sig")
        return self._transaction

    def verify_and_decode_renewal_info(self, _payload: str) -> dict[str, Any]:
        if self._inner_fail:
            raise make_verification_error("bad inner sig")
        return self._renewal


def notification_dict(
    *,
    raw_type: str,
    signed_txn: str | None = "signed-txn",
    signed_renewal: str | None = "signed-renewal",
) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if signed_txn is not None:
        data["signedTransactionInfo"] = signed_txn
    if signed_renewal is not None:
        data["signedRenewalInfo"] = signed_renewal
    return {"rawNotificationType": raw_type, "data": data}
