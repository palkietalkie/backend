# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Price every subscription in `app/iap/subscriptions_list.py` across all App Store territories.

A subscription available in a territory with no price stays `MISSING_METADATA`. Anchoring only the USA base price is not enough — Apple does not auto-fill the other 174 territories — so this walks the USA base point's `equalizations` (Apple's currency-converted equivalent per territory) and schedules a price for each, USA included. This is the only pricing step; it establishes the full price set from scratch.

All prices go in ONE PATCH per subscription because PATCHing the to-many `prices` relationship REPLACES the set, so a chunked approach would wipe earlier batches; the single PATCH declares the full territory list (USA base + 174 equalized) at once.

Idempotent: skips a subscription already priced in every available territory.

Run: `cd backend && uv run scripts/asc/equalize_subscription_prices.py [product_id ...]` — a trailing product-id filter limits the run to those subscriptions (validate on one before all four).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.constants import BASE_TERRITORY  # noqa: E402
from scripts.asc.find_subscription_price_point import find_subscription_price_point  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.list_priced_territories import list_priced_territories  # noqa: E402
from scripts.asc.list_territory_price_points import list_territory_price_points  # noqa: E402
from scripts.asc.schedule_all_subscription_prices import (  # noqa: E402
    schedule_all_subscription_prices,
)


def equalize_subscription_prices() -> None:
    only = set(sys.argv[1:])
    with get_asc_client() as client:
        for s in SUBSCRIPTIONS:
            if only and s.product_id not in only:
                continue
            base_point = find_subscription_price_point(
                client, s.asc_id, BASE_TERRITORY, s.target_usd_price
            )
            if base_point is None:
                print(f"[asc] {s.product_id}: no USA price point for ${s.target_usd_price}")
                continue
            points = list_territory_price_points(client, base_point)
            have = list_priced_territories(client, s.asc_id)
            if have >= points.keys():
                print(f"[asc] {s.product_id}: already priced in {len(have)} territories")
                continue
            status, body = schedule_all_subscription_prices(client, s.asc_id, points)
            if status >= 300:
                print(f"[asc] {s.product_id}: FAIL {status} {body[:400]}")
                continue
            print(f"[asc] {s.product_id}: priced {len(points)} territories")


if __name__ == "__main__":
    equalize_subscription_prices()
