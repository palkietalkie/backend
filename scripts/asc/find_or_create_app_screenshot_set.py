import httpx


def find_or_create_app_screenshot_set(
    client: httpx.Client, version_localization_id: str, display_type: str
) -> str:
    """Return the id of the `appScreenshotSet` for one display type on a version localization, creating it if absent (idempotent)."""
    r = client.get(
        f"/v1/appStoreVersionLocalizations/{version_localization_id}/appScreenshotSets"
        "?fields[appScreenshotSets]=screenshotDisplayType&limit=50"
    )
    r.raise_for_status()
    for row in r.json().get("data", []):
        if row.get("attributes", {}).get("screenshotDisplayType") == display_type:
            return str(row["id"])
    payload = {
        "data": {
            "type": "appScreenshotSets",
            "attributes": {"screenshotDisplayType": display_type},
            "relationships": {
                "appStoreVersionLocalization": {
                    "data": {"type": "appStoreVersionLocalizations", "id": version_localization_id},
                },
            },
        }
    }
    r = client.post("/v1/appScreenshotSets", json=payload)
    r.raise_for_status()
    return str(r.json()["data"]["id"])
