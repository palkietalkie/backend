import pytest

from app.services.apple_asn._fakes import FakeVerifier, build_notification_dict
from app.services.apple_asn.exceptions import InvalidSignatureError
from app.services.apple_asn.verify_and_decode import verify_and_decode


def test_verify_and_decode_outer_signature_failure() -> None:
    verifier = FakeVerifier(
        notification=build_notification_dict(raw_type="SUBSCRIBED"), outer_fail=True
    )
    with pytest.raises(InvalidSignatureError):
        verify_and_decode(verifier, "doesntmatter")


def test_verify_and_decode_returns_raw_type() -> None:
    notif = build_notification_dict(raw_type="DID_RENEW")
    verifier = FakeVerifier(notification=notif)
    _, raw_type = verify_and_decode(verifier, "p")
    assert raw_type == "DID_RENEW"
