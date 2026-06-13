from typing import Any

import httpx


def schedule_all_subscription_prices(
    client: httpx.Client, sub_id: str, points: dict[str, str]
) -> tuple[int, str]:
    """Schedule a price for every territory in `points` in ONE PATCH, returning (status, body).

    Apple rejects a direct `POST /v1/subscriptionPrices`, so each price is declared inline under `included` and referenced from the subscription's `prices` relationship by a local-only id (the `${…}` placeholders) — Apple links them atomically. All territories go in the single PATCH because PATCHing the to-many `prices` relationship REPLACES the set, so writing in chunks would wipe earlier batches.
    """
    included: list[dict[str, Any]] = []
    refs: list[dict[str, str]] = []
    for territory, point_id in points.items():
        local_id = f"${{price-{territory}}}"
        refs.append({"type": "subscriptionPrices", "id": local_id})
        included.append(
            {
                "type": "subscriptionPrices",
                "id": local_id,
                "attributes": {"preserveCurrentPrice": False},
                "relationships": {
                    "subscription": {"data": {"type": "subscriptions", "id": sub_id}},
                    "territory": {"data": {"type": "territories", "id": territory}},
                    "subscriptionPricePoint": {
                        "data": {"type": "subscriptionPricePoints", "id": point_id}
                    },
                },
            }
        )
    payload = {
        "data": {
            "type": "subscriptions",
            "id": sub_id,
            "relationships": {"prices": {"data": refs}},
        },
        "included": included,
    }
    r = client.patch(f"/v1/subscriptions/{sub_id}", json=payload)
    return r.status_code, r.text
