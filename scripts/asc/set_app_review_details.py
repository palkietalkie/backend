# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Push the App Store review contact + sign-in notes (app/asc/app_review_info.py SSoT) to ASC.

The app is SSO-only, so there's no demo account; the notes tell the reviewer to use Sign in with Apple. Sets the appStoreReviewDetail on the editable (PREPARE_FOR_SUBMISSION) version, creating it if absent.

Run: `cd backend && uv run scripts/asc/set_app_review_details.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.asc.app_review_info import (  # noqa: E402
    DEMO_ACCOUNT_REQUIRED,
    REVIEW_CONTACT,
    REVIEW_NOTES,
)
from scripts.asc.constants import APP_ID, EDITABLE_VERSION_STATES  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402


def set_app_review_details() -> None:
    attributes = {
        "contactFirstName": REVIEW_CONTACT["first_name"],
        "contactLastName": REVIEW_CONTACT["last_name"],
        "contactPhone": REVIEW_CONTACT["phone"],
        "contactEmail": REVIEW_CONTACT["email"],
        "demoAccountRequired": DEMO_ACCOUNT_REQUIRED,
        "notes": REVIEW_NOTES,
    }
    with get_asc_client() as client:
        versions = client.get(f"/v1/apps/{APP_ID}/appStoreVersions?limit=50")
        versions.raise_for_status()
        version_id = next(
            (
                str(v["id"])
                for v in versions.json()["data"]
                if v.get("attributes", {}).get("appStoreState") in EDITABLE_VERSION_STATES
            ),
            None,
        )
        if version_id is None:
            sys.exit(
                f"no version in an editable state ({', '.join(sorted(EDITABLE_VERSION_STATES))})"
            )

        existing = client.get(f"/v1/appStoreVersions/{version_id}/appStoreReviewDetail")
        current = existing.json().get("data") if existing.status_code < 300 else None
        if current:
            detail_id = str(current["id"])
            resp = client.patch(
                f"/v1/appStoreReviewDetails/{detail_id}",
                json={
                    "data": {
                        "type": "appStoreReviewDetails",
                        "id": detail_id,
                        "attributes": attributes,
                    }
                },
            )
        else:
            resp = client.post(
                "/v1/appStoreReviewDetails",
                json={
                    "data": {
                        "type": "appStoreReviewDetails",
                        "attributes": attributes,
                        "relationships": {
                            "appStoreVersion": {
                                "data": {"type": "appStoreVersions", "id": version_id}
                            }
                        },
                    }
                },
            )
        if resp.status_code >= 300:
            sys.exit(f"FAIL: set review details: {resp.status_code} {resp.text}")
    print("[asc] review details set (Sign in with Apple notes, no demo account required)")


if __name__ == "__main__":
    set_app_review_details()
