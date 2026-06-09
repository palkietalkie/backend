from typing import Any

import httpx


def schedule_subscription_price(
    client: httpx.Client, sub_id: str, territory: str, price_point_id: str
) -> tuple[int, str]:
    """PATCH the subscription with a new price, using Apple's JSON:API inline-create pattern.

    Apple rejects direct POST /v1/subscriptionPrices with `ENTITY_ERROR.RELATIONSHIP.INVALID` on the `subscriptionPricePoint` pointer — the only working path is to PATCH the parent subscription with the new price declared inline under `included` and referenced from `relationships.prices` by a local-only id. Apple links them atomically.

    Returns `(status_code, response_text)` so the caller can decide how to report.
    """
    local_id = "${new-price}"
    payload: dict[str, Any] = {
        "data": {
            "type": "subscriptions",
            "id": sub_id,
            "relationships": {
                "prices": {"data": [{"type": "subscriptionPrices", "id": local_id}]},
            },
        },
        "included": [
            {
                "type": "subscriptionPrices",
                "id": local_id,
                "attributes": {"preserveCurrentPrice": False},
                "relationships": {
                    "subscription": {"data": {"type": "subscriptions", "id": sub_id}},
                    "territory": {"data": {"type": "territories", "id": territory}},
                    "subscriptionPricePoint": {
                        "data": {
                            "type": "subscriptionPricePoints",
                            "id": price_point_id,
                        }
                    },
                },
            }
        ],
    }
    r = client.patch(f"/v1/subscriptions/{sub_id}", json=payload)
    return r.status_code, r.text
