# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Upload one App Review screenshot per subscription declared in `app/iap/subscriptions_list.py`.

Orchestrator only — Apple's 3-step asset upload is split across `reserve_review_screenshot` (POST the metadata + get presigned upload ops), `upload_screenshot_bytes` (PUT the file bytes per op), and `commit_review_screenshot` (PATCH `uploaded=true` + md5). Idempotent: skips any subscription that already has a screenshot.

Run: `cd backend && APPLE_ASC_ISSUER_ID=… APPLE_ASC_KEY_ID=… uv run scripts/asc/upload_iap_screenshots.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.iap.subscriptions_list import SUBSCRIPTIONS  # noqa: E402
from scripts.asc.commit_review_screenshot import commit_review_screenshot  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.reserve_review_screenshot import reserve_review_screenshot  # noqa: E402
from scripts.asc.upload_screenshot_bytes import upload_screenshot_bytes  # noqa: E402

SCREENSHOTS_DIR = Path(__file__).resolve().parents[2] / "secrets" / "iap_screenshots"


def main() -> None:
    with get_asc_client() as client:
        for s in SUBSCRIPTIONS:
            r = client.get(f"/v1/subscriptions/{s.asc_id}/appStoreReviewScreenshot")
            if r.status_code == 200 and r.json().get("data"):
                print(f"[asc] {s.product_id}: screenshot already uploaded")
                continue

            png = SCREENSHOTS_DIR / f"{s.asc_id}.png"
            if not png.exists():
                print(
                    f"[asc] {s.product_id}: missing {png.name} — "
                    f"run generate_iap_screenshots.py first"
                )
                continue

            reserved = reserve_review_screenshot(client, s.asc_id, png)
            upload_screenshot_bytes(png, reserved["attributes"]["uploadOperations"])
            commit_review_screenshot(client, reserved["id"], png)
            print(f"[asc] {s.product_id}: uploaded {png.name}")


if __name__ == "__main__":
    main()
