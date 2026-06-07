# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Enable every subscription declared in `app/iap/subscriptions_list.py` in every Apple territory.

Each subscription has a `subscriptionAvailability` resource holding the list of territories the IAP is sellable in. Without it, every territory counter shows "0" in ASC and the product is unbuyable anywhere — even after a USA price is set.

Pattern: POST /v1/subscriptionAvailabilities once per subscription, with the full list of territory IDs and `availableInNewTerritories=true` so any territory Apple later adds is auto-enabled.

Run: `cd backend && APPLE_ASC_ISSUER_ID=… APPLE_ASC_KEY_ID=… uv run app/scripts/asc/set_iap_availability.py`
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.paginate import paginate  # noqa: E402


def main() -> None:
    with get_asc_client() as client:
        territories = paginate(client, "/v1/territories?limit=200")
        territory_ids = [t["id"] for t in territories]
        print(f"[asc] {len(territory_ids)} territories from Apple")

        for s in SUBSCRIPTIONS:
            r = client.get(f"/v1/subscriptions/{s.asc_id}/subscriptionAvailability")
            if r.status_code == 200:
                print(f"[asc] {s.product_id}: availability already set")
                continue

            payload: dict[str, Any] = {
                "data": {
                    "type": "subscriptionAvailabilities",
                    "attributes": {"availableInNewTerritories": True},
                    "relationships": {
                        "subscription": {"data": {"type": "subscriptions", "id": s.asc_id}},
                        "availableTerritories": {
                            "data": [{"type": "territories", "id": tid} for tid in territory_ids]
                        },
                    },
                }
            }
            r = client.post("/v1/subscriptionAvailabilities", json=payload)
            if r.status_code >= 300:
                print(f"[asc] {s.product_id}: FAIL {r.status_code} {r.text[:300]}")
                continue
            print(f"[asc] {s.product_id}: enabled in {len(territory_ids)} territories")


if __name__ == "__main__":
    main()
