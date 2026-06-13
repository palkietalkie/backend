from typing import Any

import httpx

from scripts.asc.constants import EDITABLE_STATE


def find_editable_version_localization(
    client: httpx.Client, app_id: str, locale: str
) -> dict[str, Any] | None:
    """Return the editable `appStoreVersionLocalizations` row for this locale, or None.

    description / keywords / promotionalText / supportUrl / marketingUrl hang off the `appStoreVersion`, so we take the version in PREPARE_FOR_SUBMISSION and find its localization for this locale.
    """
    r = client.get(f"/v1/apps/{app_id}/appStoreVersions?limit=50")
    r.raise_for_status()
    version_id: str | None = None
    for v in r.json().get("data", []):
        if v.get("attributes", {}).get("appStoreState") == EDITABLE_STATE:
            version_id = str(v["id"])
            break
    if version_id is None:
        return None
    r = client.get(f"/v1/appStoreVersions/{version_id}/appStoreVersionLocalizations?limit=50")
    r.raise_for_status()
    for row in r.json().get("data", []):
        if row.get("attributes", {}).get("locale") == locale:
            return row
    return None
