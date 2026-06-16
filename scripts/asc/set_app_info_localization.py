import httpx

from app.asc.listing import Listing
from scripts.asc.diff_attributes import diff_attributes
from scripts.asc.find_editable_app_info_localization import find_editable_app_info_localization
from scripts.asc.patch_localization import patch_localization


def set_app_info_localization(client: httpx.Client, app_id: str, listing: Listing) -> None:
    """Reconcile name + subtitle + privacyPolicyUrl on the appInfo localization for one locale (idempotent)."""
    row = find_editable_app_info_localization(client, app_id, listing.locale)
    if row is None:
        print(f"[asc] {listing.locale} appInfo: no editable localization found")
        return
    desired = {
        "name": listing.name,
        "subtitle": listing.subtitle,
        "privacyPolicyUrl": listing.privacy_policy_url,
    }
    changed = diff_attributes(row.get("attributes", {}), desired)
    if not changed:
        print(f"[asc] {listing.locale} appInfo (name, subtitle, privacyPolicyUrl): up to date")
        return
    patch_localization(client, "appInfoLocalizations", str(row["id"]), changed, listing.locale)
