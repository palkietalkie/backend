from typing import Any

import httpx

from scripts.asc.paginate import paginate


def list_subscription_prices(client: httpx.Client, sub_id: str) -> list[dict[str, Any]]:
    """Return every scheduled `subscriptionPrices` row for this subscription, eager-loading `subscriptionPricePoint`.

    Caller uses the included pricePoint relationship to dedupe — re-PATCHing a price that's already scheduled at the same point is a no-op but wastes a round trip.
    """
    return paginate(
        client,
        f"/v1/subscriptions/{sub_id}/prices?include=subscriptionPricePoint&limit=200",
    )
