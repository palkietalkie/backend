from pathlib import Path
from typing import Any

import httpx


def reserve_review_screenshot(client: httpx.Client, sub_id: str, png: Path) -> dict[str, Any]:
    """Step 1 of Apple's 3-step screenshot upload: tell ASC the file size + name, get back the asset envelope with one or more `uploadOperations` describing where to PUT the bytes.

    Returns the full `data` block (asset id + attributes); caller passes `attributes.uploadOperations` to `upload_screenshot_bytes` and the asset id to `commit_review_screenshot`.
    """
    payload: dict[str, Any] = {
        "data": {
            "type": "subscriptionAppStoreReviewScreenshots",
            "attributes": {"fileSize": png.stat().st_size, "fileName": png.name},
            "relationships": {
                "subscription": {"data": {"type": "subscriptions", "id": sub_id}},
            },
        }
    }
    r = client.post("/v1/subscriptionAppStoreReviewScreenshots", json=payload)
    r.raise_for_status()
    data: dict[str, Any] = r.json()["data"]
    return data
