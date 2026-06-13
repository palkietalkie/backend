import httpx

from scripts.asc.paginate import paginate


def list_priced_territories(client: httpx.Client, sub_id: str) -> set[str]:
    """Return the set of territory ids that already have a price scheduled for this subscription."""
    rows = paginate(client, f"/v1/subscriptions/{sub_id}/prices?include=territory&limit=200")
    return {
        territory
        for p in rows
        if (territory := p.get("relationships", {}).get("territory", {}).get("data", {}).get("id"))
    }
