import time
from pathlib import Path

import jwt

from app.apple_identifiers import APPLE_ISSUER_ID
from scripts.asc.constants import ASC_KEY_ID
from scripts.asc.require_env import require_env


def mint_jwt() -> str:
    """Sign a 20-minute App Store Connect API JWT (ES256) using the locally-stored .p8.

    Reads the private key (the only secret) from `backend/secrets/apple_asc_api.p8` when present, otherwise from the `APPLE_ASC_PRIVATE_KEY` env var (set in CI). Issuer + Key id are non-secret constants. Apple caps token lifetime at 60 min — 20 is a safe headroom.
    """
    pem_path = Path(__file__).resolve().parents[2] / "secrets" / "apple_asc_api.p8"
    pem = pem_path.read_text() if pem_path.exists() else require_env("APPLE_ASC_PRIVATE_KEY")
    now = int(time.time())
    return jwt.encode(
        {
            "iss": APPLE_ISSUER_ID,
            "iat": now,
            "exp": now + 20 * 60,
            "aud": "appstoreconnect-v1",
        },
        pem,
        algorithm="ES256",
        headers={"alg": "ES256", "kid": ASC_KEY_ID, "typ": "JWT"},
    )
