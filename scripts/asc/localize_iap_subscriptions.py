# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Reconcile every locale declared in `app/iap/subscriptions_list.py` against ASC.

Without at least one localization (display name + description) per subscription, Apple holds the subscription in `MISSING_METADATA` and refuses submission. Each subscription's `localizations` tuple is the canonical list of strings — extend or edit it there, never inline here.

Display name limit: 30 chars. Description limit: 45 chars. Both surface in the App Store and the iOS purchase sheet.

Idempotent upsert: POSTs a new localization if (subscription, locale) is missing; PATCHes the existing row if its name/description drifts from the canonical list; no-ops if both match.

Run: `cd backend && uv run scripts/asc/localize_iap_subscriptions.py`
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
        for s in SUBSCRIPTIONS:
            existing = paginate(
                client,
                f"/v1/subscriptions/{s.asc_id}/subscriptionLocalizations?limit=200",
            )
            by_locale = {e.get("attributes", {}).get("locale"): e for e in existing}
            for loc in s.localizations:
                row = by_locale.get(loc.locale)
                if row is None:
                    payload: dict[str, Any] = {
                        "data": {
                            "type": "subscriptionLocalizations",
                            "attributes": {
                                "name": loc.name,
                                "locale": loc.locale,
                                "description": loc.description,
                            },
                            "relationships": {
                                "subscription": {"data": {"type": "subscriptions", "id": s.asc_id}},
                            },
                        }
                    }
                    r = client.post("/v1/subscriptionLocalizations", json=payload)
                    if r.status_code >= 300:
                        print(
                            f"[asc] {s.product_id} {loc.locale}: FAIL {r.status_code} {r.text[:300]}"
                        )
                        continue
                    print(f"[asc] {s.product_id} {loc.locale}: created '{loc.name}'")
                    continue
                attrs = row.get("attributes", {})
                if attrs.get("name") == loc.name and attrs.get("description") == loc.description:
                    print(f"[asc] {s.product_id} {loc.locale}: up to date")
                    continue
                payload = {
                    "data": {
                        "type": "subscriptionLocalizations",
                        "id": row["id"],
                        "attributes": {
                            "name": loc.name,
                            "description": loc.description,
                        },
                    }
                }
                r = client.patch(f"/v1/subscriptionLocalizations/{row['id']}", json=payload)
                if r.status_code >= 300:
                    print(f"[asc] {s.product_id} {loc.locale}: FAIL {r.status_code} {r.text[:300]}")
                    continue
                print(f"[asc] {s.product_id} {loc.locale}: updated -> '{loc.description}'")


if __name__ == "__main__":
    main()
