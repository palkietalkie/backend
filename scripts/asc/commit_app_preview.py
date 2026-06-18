import hashlib
import sys
from pathlib import Path
from typing import Any

import httpx


def commit_app_preview(client: httpx.Client, preview_id: str, video: Path) -> None:
    """Step 3 of Apple's 3-step upload for an App Preview video: PATCH the asset with `uploaded=true` + the file's md5 so Apple finalizes it, then transcodes it asynchronously (assetDeliveryState goes COMPLETE once processing succeeds).

    Apple specifies md5 (S324) for `sourceFileChecksum` — a content-integrity tag, not a security primitive. Aborts on non-2xx since a half-uploaded asset is worse than none.
    """
    md5_hex = hashlib.md5(video.read_bytes()).hexdigest()  # noqa: S324 — Apple specifies md5 for sourceFileChecksum
    payload: dict[str, Any] = {
        "data": {
            "type": "appPreviews",
            "id": preview_id,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5_hex},
        }
    }
    r = client.patch(f"/v1/appPreviews/{preview_id}", json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: commit {preview_id}: {r.status_code} {r.text}")
