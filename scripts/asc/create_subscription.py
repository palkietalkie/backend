import sys
from typing import Any

import httpx

from app.iap.subscription import Subscription


def create_subscription(client: httpx.Client, group_id: str, subscription: Subscription) -> str:
    """Create a single subscription IAP under the given group, return the new ASC subscription id.

    Sets the product id, family-share flag, and subscription period from the canonical `Subscription` row. Other artifacts — availability, price, localization, screenshot, submission — are owned by sibling scripts and run after creation.
    """
    payload: dict[str, Any] = {
        "data": {
            "type": "subscriptions",
            "attributes": {
                "name": subscription.asc_reference_name,
                "productId": subscription.product_id,
                "familySharable": subscription.family_shareable,
                "subscriptionPeriod": subscription.subscription_period,
                "reviewNote": "Created via ASC API by create_iap_subscriptions.py",
            },
            "relationships": {
                "group": {"data": {"type": "subscriptionGroups", "id": group_id}},
            },
        }
    }
    r = client.post("/v1/subscriptions", json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: create sub {subscription.product_id}: {r.status_code} {r.text}")
    return str(r.json()["data"]["id"])
