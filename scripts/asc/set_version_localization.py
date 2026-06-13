import httpx

from app.asc.listing import Listing
from scripts.asc.diff_attributes import diff_attributes
from scripts.asc.find_editable_version_localization import find_editable_version_localization
from scripts.asc.patch_localization import patch_localization


def set_version_localization(client: httpx.Client, app_id: str, listing: Listing) -> None:
    """Reconcile description / keywords / promo / support / marketing on the version localization (idempotent)."""
    row = find_editable_version_localization(client, app_id, listing.locale)
    if row is None:
        print(f"[asc] {listing.locale} version: no editable localization found")
        return
    desired = {
        "description": listing.description,
        "keywords": listing.keywords,
        "promotionalText": listing.promotional_text,
        "supportUrl": listing.support_url,
        "marketingUrl": listing.marketing_url,
    }
    changed = diff_attributes(row.get("attributes", {}), desired)
    if not changed:
        print(
            f"[asc] {listing.locale} version "
            "(description, keywords, promotionalText, supportUrl, marketingUrl): up to date"
        )
        return
    patch_localization(
        client, "appStoreVersionLocalizations", str(row["id"]), changed, listing.locale
    )
