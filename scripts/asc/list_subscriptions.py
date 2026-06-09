import httpx


def list_subscriptions(client: httpx.Client, group_id: str) -> dict[str, str]:
    """Return a `{productId: subscriptionId}` map for every subscription in the group.

    Callers use this to skip product creation when one with the same product id already exists.
    """
    r = client.get(f"/v1/subscriptionGroups/{group_id}/subscriptions?limit=200")
    r.raise_for_status()
    return {sub["attributes"]["productId"]: sub["id"] for sub in r.json().get("data", [])}
