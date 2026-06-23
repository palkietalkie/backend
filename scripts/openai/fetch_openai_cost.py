import datetime as dt
from urllib.parse import urlencode

import httpx

from scripts.read_env_value import read_env_value

_COSTS_URL = "https://api.openai.com/v1/organization/costs"


def fetch_openai_cost(since: dt.date) -> tuple[float, dict[str, float]]:
    """Actual billed OpenAI org cost from `since` (UTC day start) to now, as (total_usd, by_line_item).

    Uses OPENAI_ADMIN_KEY: the Costs API is account-level and the project OPENAI_API_KEY can't read it. Daily buckets, paginated. amount.value arrives as a high-precision decimal string. line_item splits cost by model + component (e.g. "gpt-realtime-2025-08-28 audio, input"), which is how we see the mini-vs-full mix.
    """
    key = read_env_value("OPENAI_ADMIN_KEY")
    if not key:
        raise SystemExit("OPENAI_ADMIN_KEY not set in backend/.env")
    start_ts = int(dt.datetime(since.year, since.month, since.day, tzinfo=dt.UTC).timestamp())

    total = 0.0
    by_item: dict[str, float] = {}
    page: str | None = None
    with httpx.Client(timeout=30.0, headers={"Authorization": f"Bearer {key}"}) as client:
        while True:
            # Literal group_by[] bracket key is what OpenAI expects; build the query by hand so it isn't percent-mangled.
            query = urlencode({"start_time": start_ts, "bucket_width": "1d", "limit": 180})
            query += "&group_by[]=line_item" + (f"&page={page}" if page else "")
            resp = client.get(f"{_COSTS_URL}?{query}")
            resp.raise_for_status()
            data = resp.json()
            for bucket in data.get("data", []):
                for res in bucket.get("results", []):
                    value = float(res["amount"]["value"])
                    total += value
                    item = res.get("line_item") or "(uncategorized)"
                    by_item[item] = by_item.get(item, 0.0) + value
            if data.get("has_more") and data.get("next_page"):
                page = data["next_page"]
            else:
                return total, by_item
