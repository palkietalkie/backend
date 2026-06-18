import hashlib
import sys
from pathlib import Path
from typing import Any

import httpx


def commit_app_screenshot(client: httpx.Client, screenshot_id: str, png: Path) -> None:
    """Step 3 of Apple's 3-step upload for a version screenshot: PATCH the asset with `uploaded=true` + the file's md5 so Apple finalizes it.

    Apple specifies md5 (S324) for `sourceFileChecksum` — a content-integrity tag, not a security primitive. Aborts on non-2xx since a half-uploaded asset is worse than none.
    """
    md5_hex = hashlib.md5(png.read_bytes()).hexdigest()  # noqa: S324 — Apple specifies md5 for sourceFileChecksum
    payload: dict[str, Any] = {
        "data": {
            "type": "appScreenshots",
            "id": screenshot_id,
            "attributes": {"uploaded": True, "sourceFileChecksum": md5_hex},
        }
    }
    r = client.patch(f"/v1/appScreenshots/{screenshot_id}", json=payload)
    if r.status_code >= 300:
        sys.exit(f"FAIL: commit {screenshot_id}: {r.status_code} {r.text}")
