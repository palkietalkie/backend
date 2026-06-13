import sys
from typing import Any

import httpx

from app.apple_identifiers import APPLE_BUNDLE_ID


def find_app_id(client: httpx.Client) -> str:
    """Return the ASC app id (numeric string) for the app's bundle id.

    The bundle id is the same one xcodegen writes into Info.plist; if the app hasn't been registered in ASC under that bundle id yet, this is a hard error — abort the calling script.
    """
    r = client.get(f"/v1/apps?filter[bundleId]={APPLE_BUNDLE_ID}&limit=1")
    r.raise_for_status()
    data: list[dict[str, Any]] = r.json().get("data", [])
    if not data:
        sys.exit(f"FAIL: app with bundleId={APPLE_BUNDLE_ID} not found in ASC.")
    return str(data[0]["id"])
