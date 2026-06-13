"""Non-secret Apple identifiers used by the runtime (and shared with tooling).

These appear in the `iss`/`kid` claims of every signed Apple JWT (anyone holding a signed token can read them) and on the public App Store listing, so they are NOT secrets — only the matching `.p8` private keys are. They live here, not in env / config / cloud secret stores, because the values are fixed constants, not per-environment configuration. Consumers import them directly; nothing re-exports them.

Scripts-only Apple constants (the ASC management key id, the ASC numeric app id) live in `scripts/asc/constants.py` instead — runtime never touches those."""

APPLE_ISSUER_ID = "129df326-897e-414d-acda-0e89b6b4f653"
"""Issuer ID of every App Store Connect API key — the JWT `iss` claim for ASC, StoreKit, and ASN. A team-level UUID; do NOT confuse with the short code-signing Team ID `7P7YY88H3V`."""

APPLE_BUNDLE_ID = "com.palkietalkie.app"
"""iOS bundle id. Matches `ios/project.yml`; the App Store Server library verifies signed ASN payloads against it, and APNs uses it as the push topic."""

STOREKIT_KEY_ID = "BVB84H5GUG"
"""Key ID of the App Store Server API key (IAP transaction lookup / ASN call-back). Matching `.p8` is secret."""
