from typing import Any

import httpx

from scripts.asc.constants import ASC_BASE


def paginate(client: httpx.Client, path: str) -> list[dict[str, Any]]:
    """Walk every page of an ASC collection endpoint, concatenating `data` entries.

    Apple returns up to 200 per page (limit param) with a `links.next` URL for the next page. The next URL is absolute (includes the host); strip the base so httpx routes through the same client baseURL.
    """
    out: list[dict[str, Any]] = []
    cursor = path
    while cursor:
        r = client.get(cursor)
        r.raise_for_status()
        body = r.json()
        out.extend(body.get("data", []))
        cursor = body.get("links", {}).get("next")
        if cursor and cursor.startswith(ASC_BASE):
            cursor = cursor[len(ASC_BASE) :]
    return out
