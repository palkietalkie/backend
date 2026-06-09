# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Set the USA price on each subscription declared in `app/iap/subscriptions_list.py`.

Orchestrator only — `find_subscription_price_point`, `list_subscription_prices`, and `schedule_subscription_price` are the sibling files that do the actual ASC API work. Apple's pricing model maps each currency/amount combination to a unique opaque `subscriptionPricePoints` id; we look up that id by target dollar amount and PATCH it onto the subscription. Apple auto-converts to other territories using the USA base.

Idempotent: skips any subscription whose current USA price point already matches the target.

Run: `cd backend && APPLE_ASC_ISSUER_ID=… APPLE_ASC_KEY_ID=… uv run scripts/asc/set_iap_prices.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.find_subscription_price_point import find_subscription_price_point  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.list_subscription_prices import list_subscription_prices  # noqa: E402
from scripts.asc.schedule_subscription_price import schedule_subscription_price  # noqa: E402

TERRITORY = "USA"


def main() -> None:
    with get_asc_client() as client:
        for s in SUBSCRIPTIONS:
            point_id = find_subscription_price_point(
                client, s.asc_id, TERRITORY, s.target_usd_price
            )
            if point_id is None:
                print(f"[asc] {s.product_id}: no USA price point for ${s.target_usd_price}")
                continue

            existing = list_subscription_prices(client, s.asc_id)
            already = any(
                p.get("relationships", {})
                .get("subscriptionPricePoint", {})
                .get("data", {})
                .get("id")
                == point_id
                for p in existing
            )
            if already:
                print(f"[asc] {s.product_id}: ${s.target_usd_price} already set")
                continue

            status, body = schedule_subscription_price(client, s.asc_id, TERRITORY, point_id)
            if status >= 300:
                print(f"[asc] {s.product_id}: FAIL {status} {body[:300]}")
                continue
            print(f"[asc] {s.product_id}: set USA ${s.target_usd_price}")


if __name__ == "__main__":
    main()
