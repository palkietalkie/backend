SOURCE = "apple_asn"

# Map from Apple wire-string notification type to ``(state, cancel_at_period_end)``.
APPLE_NOTIFICATION_TO_STATE: dict[str, tuple[str, bool]] = {
    "SUBSCRIBED": ("active", False),
    "DID_RENEW": ("active", False),
    # Cancel-at-period-end toggled.
    "DID_CHANGE_RENEWAL_STATUS": ("active", True),
    "DID_FAIL_TO_RENEW": ("active", True),
    "EXPIRED": ("inactive", False),
    "REFUND": ("revoke", False),
    "REVOKE": ("revoke", False),
}

APPLE_ROOT_URLS: tuple[str, ...] = (
    "https://www.apple.com/certificateauthority/AppleRootCA-G3.cer",
    "https://www.apple.com/certificateauthority/AppleRootCA-G2.cer",
    "https://www.apple.com/certificateauthority/AppleIncRootCertificate.cer",
)
