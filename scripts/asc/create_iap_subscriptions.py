# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Create / reconcile the auto-renewing subscription IAPs declared in `app/iap/subscriptions_list.py`.

Orchestrator only — the actual ASC API calls live in sibling files (`find_app_id`, `list_subscription_groups`, `create_subscription_group`, `list_subscriptions`, `create_subscription`). Subscription groups are derived from each product's `group_reference`.

Idempotent: skips any group / product whose reference name / product id already exists. Does NOT delete or modify existing products.

Run: `cd backend && APPLE_ASC_ISSUER_ID=… APPLE_ASC_KEY_ID=… uv run scripts/asc/create_iap_subscriptions.py`"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.constants import BUNDLE_ID  # noqa: E402
from scripts.asc.create_subscription import create_subscription  # noqa: E402
from scripts.asc.create_subscription_group import create_subscription_group  # noqa: E402
from scripts.asc.find_app_id import find_app_id  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.list_subscription_groups import list_subscription_groups  # noqa: E402
from scripts.asc.list_subscriptions import list_subscriptions  # noqa: E402


def main() -> None:
    with get_asc_client() as client:
        app_id = find_app_id(client)
        print(f"[asc] app id {app_id} for {BUNDLE_ID}")

        groups = list_subscription_groups(client, app_id)
        for ref in {s.group_reference for s in SUBSCRIPTIONS}:
            if ref not in groups:
                groups[ref] = create_subscription_group(client, app_id, ref)
                print(f"[asc] created group {ref} -> {groups[ref]}")
            else:
                print(f"[asc] group {ref} exists -> {groups[ref]}")

        for s in SUBSCRIPTIONS:
            group_id = groups[s.group_reference]
            existing = list_subscriptions(client, group_id)
            if s.product_id in existing:
                print(f"[asc] sub {s.product_id} exists -> {existing[s.product_id]}")
                continue
            sub_id = create_subscription(client, group_id, s)
            print(f"[asc] created sub {s.product_id} -> {sub_id}")

    print(json.dumps({"ok": True, "products": len(SUBSCRIPTIONS)}, indent=2))


if __name__ == "__main__":
    main()
