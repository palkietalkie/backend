# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Reconcile every subscription-group localization in `app/iap/subscription_groups_list.py` against ASC.

A subscription group with zero localizations holds every subscription inside it in `MISSING_METADATA`, blocking submission. Each group needs at least one customer-facing display name (en-US). The canonical names live in `subscription_groups_list.py` — edit there, never inline here.

Display name limit: 30 chars.

Idempotent upsert: POSTs a localization if (group, locale) is missing; PATCHes if the name drifts; no-ops if it matches. The ASC group id is discovered by matching the group's `referenceName`, so no numeric id is hardcoded.

Run: `cd backend && uv run scripts/asc/set_subscription_group_metadata.py`
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscription_groups_list import SUBSCRIPTION_GROUPS  # noqa: E402
from scripts.asc.constants import APP_ID  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.paginate import paginate  # noqa: E402


def main() -> None:
    with get_asc_client() as client:
        groups = paginate(client, f"/v1/apps/{APP_ID}/subscriptionGroups?limit=200")
        asc_id_by_reference = {
            g.get("attributes", {}).get("referenceName"): g["id"] for g in groups
        }
        for group in SUBSCRIPTION_GROUPS:
            asc_id = asc_id_by_reference.get(group.group_reference)
            if asc_id is None:
                print(f"[asc] {group.group_reference}: FAIL no ASC group with this reference name")
                continue
            existing = paginate(
                client,
                f"/v1/subscriptionGroups/{asc_id}/subscriptionGroupLocalizations?limit=200",
            )
            by_locale = {e.get("attributes", {}).get("locale"): e for e in existing}
            for loc in group.localizations:
                row = by_locale.get(loc.locale)
                if row is None:
                    payload: dict[str, Any] = {
                        "data": {
                            "type": "subscriptionGroupLocalizations",
                            "attributes": {"name": loc.name, "locale": loc.locale},
                            "relationships": {
                                "subscriptionGroup": {
                                    "data": {"type": "subscriptionGroups", "id": asc_id}
                                },
                            },
                        }
                    }
                    r = client.post("/v1/subscriptionGroupLocalizations", json=payload)
                    if r.status_code >= 300:
                        print(
                            f"[asc] {group.group_reference} {loc.locale}: FAIL {r.status_code} {r.text[:300]}"
                        )
                        continue
                    print(f"[asc] {group.group_reference} {loc.locale}: created '{loc.name}'")
                    continue
                if row.get("attributes", {}).get("name") == loc.name:
                    print(f"[asc] {group.group_reference} {loc.locale}: up to date")
                    continue
                payload = {
                    "data": {
                        "type": "subscriptionGroupLocalizations",
                        "id": row["id"],
                        "attributes": {"name": loc.name},
                    }
                }
                r = client.patch(f"/v1/subscriptionGroupLocalizations/{row['id']}", json=payload)
                if r.status_code >= 300:
                    print(
                        f"[asc] {group.group_reference} {loc.locale}: FAIL {r.status_code} {r.text[:300]}"
                    )
                    continue
                print(f"[asc] {group.group_reference} {loc.locale}: updated -> '{loc.name}'")


if __name__ == "__main__":
    main()
