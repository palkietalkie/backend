# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Set the app's Content Rights declaration on App Store Connect via the API.

Palkie Talkie shows third-party content (daily news headlines + article bodies from the news API), so the declaration must be USES_THIRD_PARTY_CONTENT — declaring DOES_NOT would be false and is a review risk. This is an app-level attribute (`contentRightsDeclaration` on the `apps` resource), so one PATCH covers it. Idempotent: skips when already set.

Run: `cd backend && uv run scripts/asc/set_content_rights.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.asc.find_app_id import find_app_id  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402

DECLARATION = "USES_THIRD_PARTY_CONTENT"


def set_content_rights() -> None:
    with get_asc_client() as client:
        app_id = find_app_id(client)
        current = client.get(f"/v1/apps/{app_id}?fields[apps]=contentRightsDeclaration")
        current.raise_for_status()
        live = current.json()["data"]["attributes"].get("contentRightsDeclaration")
        if live == DECLARATION:
            print(f"[asc] content rights already {DECLARATION}")
            return
        resp = client.patch(
            f"/v1/apps/{app_id}",
            json={
                "data": {
                    "type": "apps",
                    "id": app_id,
                    "attributes": {"contentRightsDeclaration": DECLARATION},
                }
            },
        )
        if resp.status_code >= 300:
            sys.exit(f"FAIL: set content rights: {resp.status_code} {resp.text}")
        print(f"[asc] content rights set {live} -> {DECLARATION}")


if __name__ == "__main__":
    set_content_rights()
