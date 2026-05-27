from app.services.apple_asn.decide_state import decide_state


def test_decide_state_known_types() -> None:
    assert decide_state("SUBSCRIBED") == ("active", False)
    assert decide_state("DID_RENEW") == ("active", False)
    assert decide_state("DID_FAIL_TO_RENEW") == ("active", True)
    assert decide_state("EXPIRED") == ("inactive", False)
    assert decide_state("REFUND") == ("revoke", False)
    assert decide_state("REVOKE") == ("revoke", False)


def test_decide_state_unknown_or_empty() -> None:
    assert decide_state("UNKNOWN_TYPE") is None
    assert decide_state("") is None
    assert decide_state(None) is None
