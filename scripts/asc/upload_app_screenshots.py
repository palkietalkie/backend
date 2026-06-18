# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Upload the framed App Store screenshots in scripts/asc/app_screenshots/ to the en-US version listing.

Apple's 6.9" iPhone slot is `APP_IPHONE_67` (it consolidated 6.7" + 6.9" — it accepts our 1320x2868). For each PNG (filename order = display order) we run Apple's 3-step asset upload: reserve -> PUT bytes -> commit with md5. Idempotent: existing screenshots in the set are deleted first, so a re-run replaces rather than appends.

Generate the PNGs first: `ios/scripts/capture-screenshots.sh` then `frame_screenshot`. Run: `cd backend && uv run scripts/asc/upload_app_screenshots.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.asc.commit_app_screenshot import commit_app_screenshot  # noqa: E402
from scripts.asc.constants import APP_SCREENSHOTS_DIR  # noqa: E402
from scripts.asc.find_app_id import find_app_id  # noqa: E402
from scripts.asc.find_editable_version_localization import (  # noqa: E402
    find_editable_version_localization,
)
from scripts.asc.find_or_create_app_screenshot_set import (  # noqa: E402
    find_or_create_app_screenshot_set,
)
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.reserve_app_screenshot import reserve_app_screenshot  # noqa: E402
from scripts.asc.upload_asset_bytes import upload_asset_bytes  # noqa: E402

# Apple's required 6.9" iPhone slot; it also serves 6.7" and accepts 1320x2868.
DISPLAY_TYPE = "APP_IPHONE_67"
LOCALE = "en-US"


def upload_app_screenshots() -> None:
    # Filenames are stable (overwritten each run); upload the current set in name order.
    pngs = sorted(APP_SCREENSHOTS_DIR.rglob("*.png"))
    if not pngs:
        sys.exit(
            f"no screenshots in {APP_SCREENSHOTS_DIR} — run capture-screenshots.sh + frame_app_screenshots.py first"
        )
    print(f"[asc] uploading {len(pngs)} screenshots")
    with get_asc_client() as client:
        app_id = find_app_id(client)
        loc = find_editable_version_localization(client, app_id, LOCALE)
        if loc is None:
            sys.exit(
                f"no editable {LOCALE} version localization (is a version in PREPARE_FOR_SUBMISSION?)"
            )
        set_id = find_or_create_app_screenshot_set(client, str(loc["id"]), DISPLAY_TYPE)

        # Clear existing so a re-run replaces rather than appends.
        existing = client.get(f"/v1/appScreenshotSets/{set_id}/appScreenshots?limit=50")
        existing.raise_for_status()
        for row in existing.json().get("data", []):
            client.delete(f"/v1/appScreenshots/{row['id']}").raise_for_status()

        for png in pngs:
            asset = reserve_app_screenshot(client, set_id, png)
            upload_asset_bytes(png, asset["attributes"]["uploadOperations"])
            commit_app_screenshot(client, str(asset["id"]), png)
            print(f"[asc] uploaded {png.name}")
    print(f"[asc] {len(pngs)} screenshots uploaded to {DISPLAY_TYPE}")


if __name__ == "__main__":
    upload_app_screenshots()
