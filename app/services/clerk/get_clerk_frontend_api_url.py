"""Derive a Clerk instance's Frontend API base URL from its publishable key."""

import base64


def get_clerk_frontend_api_url(publishable_key: str) -> str:
    # A Clerk publishable key is `pk_<env>_<base64(frontend_api_host + "$")>`. Decode the last segment to recover the host. Re-pad because Clerk strips base64 "=" padding.
    encoded = publishable_key.split("_", 2)[-1]
    padded = encoded + "=" * (-len(encoded) % 4)
    host = base64.b64decode(padded).decode().rstrip("$")
    return f"https://{host}"
