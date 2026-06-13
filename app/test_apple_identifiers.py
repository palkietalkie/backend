"""Lock the non-secret Apple identifiers. Runtime (ASN verify, APNs push) and tooling (scripts/asc/*) all read these, so a wrong value breaks signing/verification with no compile-time signal."""

import re

from app import apple_identifiers


def test_bundle_id_matches_app() -> None:
    assert apple_identifiers.APPLE_BUNDLE_ID == "com.palkietalkie.app"


def test_issuer_id_is_a_uuid() -> None:
    # App Store Connect issuer id = the team UUID.
    assert re.fullmatch(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        apple_identifiers.APPLE_ISSUER_ID,
    )


def test_storekit_key_id_is_apple_key_format() -> None:
    # Apple API key ids are 10-char uppercase alphanumeric.
    assert re.fullmatch(r"[A-Z0-9]{10}", apple_identifiers.STOREKIT_KEY_ID)
