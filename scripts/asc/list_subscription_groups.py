import httpx


def list_subscription_groups(client: httpx.Client, app_id: str) -> dict[str, str]:
    """Return a `{referenceName: groupId}` map for every subscription group on this app.

    Callers use this to skip group creation when one with the same reference name already exists.
    """
    r = client.get(f"/v1/apps/{app_id}/subscriptionGroups?limit=200")
    r.raise_for_status()
    return {grp["attributes"]["referenceName"]: grp["id"] for grp in r.json().get("data", [])}
