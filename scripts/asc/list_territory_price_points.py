import httpx

from scripts.asc.constants import BASE_TERRITORY
from scripts.asc.paginate import paginate


def list_territory_price_points(client: httpx.Client, base_point_id: str) -> dict[str, str]:
    """Map every App Store territory to its subscription price point id for one base price.

    The map is `{territory: price_point_id}` for all 175 territories: the USA base point plus the 174 `equalizations` Apple computes (the currency-converted equivalent of the base price in each territory).
    """
    points = {BASE_TERRITORY: base_point_id}
    rows = paginate(
        client,
        f"/v1/subscriptionPricePoints/{base_point_id}/equalizations?include=territory&limit=200",
    )
    for row in rows:
        territory = row.get("relationships", {}).get("territory", {}).get("data", {}).get("id")
        if territory:
            points[territory] = row["id"]
    return points
