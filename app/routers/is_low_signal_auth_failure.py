def is_low_signal_auth_failure(reason: str | None) -> bool:
    """True for Apple's catch-all ASAuthorizationError 1000 (.unknown) with NO underlying cause.

    iOS's diagnoseAuthError renders these as "...AuthorizationError#1000: ..." with no " ← " chain. Apple returns this same code both for benign sheet-dismissals and for devices with no usable Apple ID (not signed into iCloud, 2FA off), so on its own it is not a reliable "broken funnel" signal and must not page the channel. A 1000 that DOES carry an underlying error (" ← AKAuthenticationError…"), any other ASAuthorizationError code, or a Clerk rejection ("Clerk[…]") still pages.

    Couples to diagnoseAuthError's reason-string format (domain#code, plus " ← " before each NSUnderlyingError layer); that string is the wire contract for the announce `reason` field.
    """
    if not reason:
        return False
    # An underlying layer means the failure has a real, diagnosable cause — page it.
    if "←" in reason:
        return False
    return "AuthorizationError#1000" in reason
