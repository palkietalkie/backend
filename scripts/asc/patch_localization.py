import httpx


def patch_localization(
    client: httpx.Client, resource_type: str, row_id: str, changed: dict[str, str], label: str
) -> None:
    """PATCH a single ASC localization row with only the changed attributes and log per-field outcome."""
    payload = {"data": {"type": resource_type, "id": row_id, "attributes": changed}}
    r = client.patch(f"/v1/{resource_type}/{row_id}", json=payload)
    if r.status_code >= 300:
        print(f"[asc] {label}: FAIL {r.status_code} {r.text[:300]}")
        return
    for field in changed:
        print(f"[asc] {label} {field}: updated")
