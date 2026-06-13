# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Upload one App Review screenshot per subscription declared in `app/iap/subscriptions_list.py`.

Orchestrator only — Apple's 3-step asset upload is split across `reserve_review_screenshot` (POST the metadata + get presigned upload ops), `upload_screenshot_bytes` (PUT the file bytes per op), and `commit_review_screenshot` (PATCH `uploaded=true` + md5).

Idempotent on CONTENT: compares the local PNG's md5 to the uploaded asset's `sourceFileChecksum`. Equal -> skip. Different -> delete the stale asset and re-upload (so a regenerated/fixed screenshot actually reaches ASC; a plain "skip if any exists" would strand the old image forever). Missing -> upload.

Run: `cd backend && uv run scripts/asc/upload_iap_screenshots.py`"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.commit_review_screenshot import commit_review_screenshot  # noqa: E402
from scripts.asc.constants import IAP_SCREENSHOTS_DIR  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.reserve_review_screenshot import reserve_review_screenshot  # noqa: E402
from scripts.asc.upload_screenshot_bytes import upload_screenshot_bytes  # noqa: E402


def main() -> None:
    with get_asc_client() as client:
        for s in SUBSCRIPTIONS:
            png = IAP_SCREENSHOTS_DIR / f"{s.product_id}.png"
            if not png.exists():
                print(
                    f"[asc] {s.product_id}: missing {png.name} — "
                    f"run generate_iap_screenshots.py first"
                )
                continue
            local_md5 = hashlib.md5(png.read_bytes()).hexdigest()  # noqa: S324 — Apple uses md5 for sourceFileChecksum

            r = client.get(f"/v1/subscriptions/{s.asc_id}/appStoreReviewScreenshot")
            existing = r.json().get("data") if r.status_code == 200 else None
            if existing:
                if existing.get("attributes", {}).get("sourceFileChecksum") == local_md5:
                    print(f"[asc] {s.product_id}: screenshot up to date")
                    continue
                d = client.delete(f"/v1/subscriptionAppStoreReviewScreenshots/{existing['id']}")
                if d.status_code >= 300:
                    print(f"[asc] {s.product_id}: FAIL delete stale {d.status_code} {d.text[:200]}")
                    continue
                print(f"[asc] {s.product_id}: deleted stale screenshot, re-uploading")

            reserved = reserve_review_screenshot(client, s.asc_id, png)
            upload_screenshot_bytes(png, reserved["attributes"]["uploadOperations"])
            commit_review_screenshot(client, reserved["id"], png)
            print(f"[asc] {s.product_id}: uploaded {png.name}")


if __name__ == "__main__":
    main()
