from typing import Any

from app.services.apple_asn._sdk import VerificationException
from app.services.apple_asn.coerce_to_dict import coerce_to_dict
from app.services.apple_asn.exceptions import InvalidSignatureError


def extract_transaction_and_renewal(
    verifier: Any, notification_obj: Any
) -> tuple[dict[str, Any], dict[str, Any]]:
    notification = coerce_to_dict(notification_obj)
    data_obj = getattr(notification_obj, "data", None) or notification.get("data")
    data = coerce_to_dict(data_obj)
    signed_transaction = (
        getattr(data_obj, "signedTransactionInfo", None)
        if data_obj is not None
        else None
    ) or data.get("signedTransactionInfo")
    signed_renewal = (
        getattr(data_obj, "signedRenewalInfo", None) if data_obj is not None else None
    ) or data.get("signedRenewalInfo")
    try:
        txn = (
            coerce_to_dict(
                verifier.verify_and_decode_signed_transaction(signed_transaction)
            )
            if signed_transaction
            else {}
        )
        renewal = (
            coerce_to_dict(verifier.verify_and_decode_renewal_info(signed_renewal))
            if signed_renewal
            else {}
        )
    except VerificationException as e:
        raise InvalidSignatureError(f"Apple inner JWS verification failed: {e}") from e
    return txn, renewal
