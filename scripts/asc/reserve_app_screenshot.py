from pathlib import Path
from typing import Any

import httpx


def reserve_app_screenshot(client: httpx.Client, set_id: str, png: Path) -> dict[str, Any]:
    """Step 1 of Apple's 3-step screenshot upload, for an App Store version screenshot: declare file size + name, get back the asset envelope whose `uploadOperations` say where to PUT the bytes.

    Same dance as reserve_review_screenshot (IAP), but the resource is `appScreenshots` hung off an `appScreenshotSet`. Returns the full `data` block (asset id + attributes).
    """
    payload: dict[str, Any] = {
        "data": {
            "type": "appScreenshots",
            "attributes": {"fileSize": png.stat().st_size, "fileName": png.name},
            "relationships": {
                "appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": set_id}},
            },
        }
    }
    r = client.post("/v1/appScreenshots", json=payload)
    r.raise_for_status()
    data: dict[str, Any] = r.json()["data"]
    return data
