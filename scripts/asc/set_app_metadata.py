# /// script
# requires-python = ">=3.12"
# dependencies = ["httpx>=0.28", "pyjwt[crypto]>=2.9"]
# ///
"""Push the App Store listing copy in `app/asc/metadata/<locale>/*.txt` to App Store Connect.

The listing text is split across two ASC resources: name + subtitle live on the app-level `appInfoLocalizations`, and description + keywords + promotionalText + supportUrl + marketingUrl live on the version-level `appStoreVersionLocalizations`. This script PATCHes both for each locale in `LISTINGS`, against the editable (PREPARE_FOR_SUBMISSION) appInfo + version.

Idempotent: each field is compared to what's live and skipped when already equal, so a no-op run prints only `up to date`. Mirrors `localize_iap_subscriptions.py`.

Run: `cd backend && uv run scripts/asc/set_app_metadata.py`"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.asc.load_listings import load_listings  # noqa: E402
from scripts.asc.find_app_id import find_app_id  # noqa: E402
from scripts.asc.get_asc_client import get_asc_client  # noqa: E402
from scripts.asc.set_app_info_localization import set_app_info_localization  # noqa: E402
from scripts.asc.set_version_localization import set_version_localization  # noqa: E402


def set_app_metadata() -> None:
    with get_asc_client() as client:
        app_id = find_app_id(client)
        for listing in load_listings():
            set_app_info_localization(client, app_id, listing)
            set_version_localization(client, app_id, listing)


if __name__ == "__main__":
    set_app_metadata()
