import sys
from typing import Any

import httpx


def create_subscription_group(client: httpx.Client, app_id: str, reference_name: str) -> str:
    """Create a new subscription group on the given app and return its ASC id.

    Apple requires Family-shareable subscriptions to live in their own group so users can't hold two of the same tier simultaneously.
    """
    payload: dict[str, Any] = {
        "data": {
            "type": "subscriptionGroups",
            "attributes": {"referenceName": reference_name},
            "relationships": {"app": {"data": {"type": "apps", "id": app_id}}},
        }
    }
    r = client.post("/v1/subscriptionGroups", json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: create group {reference_name}: {r.status_code} {r.text}")
    return str(r.json()["data"]["id"])
