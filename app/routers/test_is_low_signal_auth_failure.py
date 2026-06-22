from app.routers.is_low_signal_auth_failure import is_low_signal_auth_failure


def test_bare_apple_unknown_is_low_signal() -> None:
    # The reported case: Apple's 1000 (.unknown) with no underlying cause, exactly as diagnoseAuthError renders it (no " ← " chain). This is the one we must NOT page on.
    reason = "com.apple.AuthenticationServices.AuthorizationError#1000: The operation couldn’t be completed."
    assert is_low_signal_auth_failure(reason) is True


def test_apple_unknown_with_underlying_cause_still_pages() -> None:
    # A 1000 that carries a real underlying error is diagnosable and IS a signal — must still page.
    reason = (
        "com.apple.AuthenticationServices.AuthorizationError#1000: ... "
        "← com.apple.AuthKit.AKAuthenticationError#-7026: ..."
    )
    assert is_low_signal_auth_failure(reason) is False


def test_other_apple_codes_page() -> None:
    # 1004 (.failed), 1002 (.invalidResponse) etc. are real failures, not the catch-all.
    assert (
        is_low_signal_auth_failure(
            "com.apple.AuthenticationServices.AuthorizationError#1004: failed"
        )
        is False
    )


def test_clerk_rejection_pages() -> None:
    assert (
        is_low_signal_auth_failure("Clerk[oauth_token_invalid] audience mismatch trace=abc")
        is False
    )


def test_no_reason_is_not_low_signal() -> None:
    assert is_low_signal_auth_failure(None) is False
    assert is_low_signal_auth_failure("") is False
