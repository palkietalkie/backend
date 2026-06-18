import httpx


def find_or_create_app_preview_set(
    client: httpx.Client, version_localization_id: str, preview_type: str
) -> str:
    """Return the id of the `appPreviewSet` for one preview type on a version localization, creating it if absent (idempotent).

    Mirrors `find_or_create_app_screenshot_set`, but previews key off `previewType` (e.g. `IPHONE_67`) rather than `screenshotDisplayType`.
    """
    r = client.get(
        f"/v1/appStoreVersionLocalizations/{version_localization_id}/appPreviewSets"
        "?fields[appPreviewSets]=previewType&limit=50"
    )
    r.raise_for_status()
    for row in r.json().get("data", []):
        if row.get("attributes", {}).get("previewType") == preview_type:
            return str(row["id"])
    payload = {
        "data": {
            "type": "appPreviewSets",
            "attributes": {"previewType": preview_type},
            "relationships": {
                "appStoreVersionLocalization": {
                    "data": {"type": "appStoreVersionLocalizations", "id": version_localization_id},
                },
            },
        }
    }
    r = client.post("/v1/appPreviewSets", json=payload)
    r.raise_for_status()
    return str(r.json()["data"]["id"])
