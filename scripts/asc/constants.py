from pathlib import Path

ASC_BASE = "https://api.appstoreconnect.apple.com"

# Only the in-progress (not-yet-released) appInfo / appStoreVersion is editable; a live one rejects PATCH.
EDITABLE_STATE = "PREPARE_FOR_SUBMISSION"

# ASC numeric app id for the bundle id. Stable once Apple assigns it. (find_app_id resolves the same value from the bundle id over the network.)
APP_ID = "6776366891"

# Key ID of the App Store Connect MANAGEMENT API key — used only by these scripts (mint_jwt). The issuer (= team id) and bundle id are runtime-shared, so they live in app/apple_identifiers.py. Matching .p8 is secret.
ASC_KEY_ID = "P4HBNA5WD6"

# Anchor territory for subscription pricing — set the USD price here, then equalize to all other territories.
BASE_TERRITORY = "USA"

# Git-TRACKED dir for the generated IAP review-screenshot PNGs — submission assets, so versioned and reviewable.
IAP_SCREENSHOTS_DIR = Path(__file__).resolve().parent / "iap_screenshots"
