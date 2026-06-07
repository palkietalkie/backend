import httpx

from scripts.asc.paginate import paginate


def find_subscription_price_point(
    client: httpx.Client, sub_id: str, territory: str, target_price: str
) -> str | None:
    """Return the opaque `subscriptionPricePoints` id matching the target customer price.

    Apple ties each price point to a specific (subscription, territory, amount) tuple, so the same USD price across different subscriptions returns different ids. Returns None when no point matches — caller should skip rather than guess a near-match.
    """
    pts = paginate(
        client,
        f"/v1/subscriptions/{sub_id}/pricePoints?filter[territory]={territory}&limit=200",
    )
    for pt in pts:
        if pt.get("attributes", {}).get("customerPrice") == target_price:
            return str(pt["id"])
    return None
