from pathlib import Path
from typing import Any

import httpx


def reserve_app_preview(client: httpx.Client, set_id: str, video: Path) -> dict[str, Any]:
    """Step 1 of Apple's 3-step upload for an App Preview video: declare file size + name, get back the asset envelope whose `uploadOperations` say where to PUT the bytes.

    Same dance as `reserve_app_screenshot`, but the resource is `appPreviews` hung off an `appPreviewSet`. Returns the full `data` block (asset id + attributes).
    """
    payload: dict[str, Any] = {
        "data": {
            "type": "appPreviews",
            "attributes": {"fileSize": video.stat().st_size, "fileName": video.name},
            "relationships": {
                "appPreviewSet": {"data": {"type": "appPreviewSets", "id": set_id}},
            },
        }
    }
    r = client.post("/v1/appPreviews", json=payload)
    r.raise_for_status()
    data: dict[str, Any] = r.json()["data"]
    return data
