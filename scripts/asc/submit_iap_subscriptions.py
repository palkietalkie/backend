# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Submit each subscription declared in `app/iap/subscriptions_list.py` to Apple for App Review.

Endpoint: POST /v1/subscriptionSubmissions with just the subscription relationship — Apple uses the subscription's price, availability, localizations, and review screenshot at submission time. Apple's review typically takes 24-48h.

Idempotent: skips any subscription that isn't in the `READY_TO_SUBMIT` state.

Run: `cd backend && APPLE_ASC_ISSUER_ID=… APPLE_ASC_KEY_ID=… uv run app/scripts/asc/submit_iap_subscriptions.py`
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402


def main() -> None:
    with get_asc_client() as client:
        for s in SUBSCRIPTIONS:
            r = client.get(f"/v1/subscriptions/{s.asc_id}")
            r.raise_for_status()
            state = r.json()["data"]["attributes"]["state"]
            print(f"[asc] {s.product_id} state: {state}")
            if state != "READY_TO_SUBMIT":
                continue

            payload: dict[str, Any] = {
                "data": {
                    "type": "subscriptionSubmissions",
                    "relationships": {
                        "subscription": {"data": {"type": "subscriptions", "id": s.asc_id}},
                    },
                }
            }
            r = client.post("/v1/subscriptionSubmissions", json=payload)
            if r.status_code >= 300:
                print(f"[asc] {s.product_id}: FAIL {r.status_code} {r.text[:400]}")
                continue
            print(f"[asc] {s.product_id}: submitted for review")


if __name__ == "__main__":
    main()
