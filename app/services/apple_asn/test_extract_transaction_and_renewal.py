import pytest

from app.services.apple_asn._fakes import FakeVerifier, notification_dict
from app.services.apple_asn.exceptions import InvalidSignatureError
from app.services.apple_asn.extract_transaction_and_renewal import (
    extract_transaction_and_renewal,
)
from app.services.apple_asn.verify_and_decode import verify_and_decode


def test_extract_transaction_and_renewal_inner_signature_failure() -> None:
    notif = notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(notification=notif, inner_fail=True)
    notification_obj, _ = verify_and_decode(verifier, "p")
    with pytest.raises(InvalidSignatureError):
        extract_transaction_and_renewal(verifier, notification_obj)


def test_extract_transaction_and_renewal_returns_dicts() -> None:
    notif = notification_dict(raw_type="SUBSCRIBED")
    verifier = FakeVerifier(
        notification=notif,
        transaction={"appAccountToken": "user_apple", "expiresDate": 1000},
        renewal={"autoRenewStatus": 1},
    )
    notification_obj, _ = verify_and_decode(verifier, "p")
    txn, renewal = extract_transaction_and_renewal(verifier, notification_obj)
    assert txn["appAccountToken"] == "user_apple"
    assert renewal["autoRenewStatus"] == 1


def test_extract_transaction_handles_no_signed_payloads() -> None:
    notif = notification_dict(raw_type="EXPIRED", signed_txn=None, signed_renewal=None)
    verifier = FakeVerifier(notification=notif)
    notification_obj, _ = verify_and_decode(verifier, "p")
    txn, renewal = extract_transaction_and_renewal(verifier, notification_obj)
    assert txn == {}
    assert renewal == {}
