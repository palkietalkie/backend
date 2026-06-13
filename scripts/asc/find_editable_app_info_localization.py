from typing import Any

import httpx

from scripts.asc.constants import EDITABLE_STATE


def find_editable_app_info_localization(
    client: httpx.Client, app_id: str, locale: str
) -> dict[str, Any] | None:
    """Return the editable `appInfoLocalizations` row for this locale, or None.

    name + subtitle hang off the app's `appInfo` (not the version), so we walk appInfos, take the one in PREPARE_FOR_SUBMISSION, and find its localization for this locale.
    """
    r = client.get(f"/v1/apps/{app_id}/appInfos?limit=50")
    r.raise_for_status()
    app_info_id: str | None = None
    for info in r.json().get("data", []):
        if info.get("attributes", {}).get("state") == EDITABLE_STATE:
            app_info_id = str(info["id"])
            break
    if app_info_id is None:
        return None
    r = client.get(f"/v1/appInfos/{app_info_id}/appInfoLocalizations?limit=50")
    r.raise_for_status()
    for row in r.json().get("data", []):
        if row.get("attributes", {}).get("locale") == locale:
            return row
    return None
