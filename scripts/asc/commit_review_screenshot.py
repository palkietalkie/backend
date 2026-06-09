import hashlib
import sys
from pathlib import Path
from typing import Any

import httpx


def commit_review_screenshot(client: httpx.Client, screenshot_id: str, png: Path) -> None:
    """Step 3 of Apple's 3-step screenshot upload: PATCH the asset with `uploaded=true` and the file's md5 hex digest so Apple finalizes it.

    Apple specifies md5 (S324 in ruff/bandit) for `sourceFileChecksum` — not a security primitive, just a content-integrity tag. Aborts the calling script on non-2xx since a half-uploaded asset is worse than no asset.
    """
    md5_hex = hashlib.md5(png.read_bytes()).hexdigest()  # noqa: S324 — Apple specifies md5 for sourceFileChecksum
    payload: dict[str, Any] = {
        "data": {
            "type": "subscriptionAppStoreReviewScreenshots",
            "id": screenshot_id,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5_hex},
        }
    }
    r = client.patch(f"/v1/subscriptionAppStoreReviewScreenshots/{screenshot_id}", json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: commit {screenshot_id}: {r.status_code} {r.text}")
