from pathlib import Path

ASC_BASE = "https://api.appstoreconnect.apple.com"

# Only the in-progress (not-yet-released) appInfo / appStoreVersion is editable; a live one rejects PATCH.
EDITABLE_STATE = "PREPARE_FOR_SUBMISSION"

# A version's review detail / metadata stays editable for (re)submission both before the first submit and after review kicks it back; a live (READY_FOR_SALE) version rejects PATCH. Used when updating a version we intend to resubmit, which may currently be REJECTED.
EDITABLE_VERSION_STATES = frozenset(
    {"PREPARE_FOR_SUBMISSION", "REJECTED", "METADATA_REJECTED", "DEVELOPER_REJECTED"}
)

# ASC numeric app id for the bundle id. Stable once Apple assigns it. (find_app_id resolves the same value from the bundle id over the network.)
APP_ID = "6776366891"

# Key ID of the App Store Connect MANAGEMENT API key — used only by these scripts (mint_jwt). The issuer (= team id) and bundle id are runtime-shared, so they live in app/apple_identifiers.py. Matching .p8 is secret.
ASC_KEY_ID = "P4HBNA5WD6"

# Anchor territory for subscription pricing — set the USD price here, then equalize to all other territories.
BASE_TERRITORY = "USA"

# Git-TRACKED dir for the generated IAP review-screenshot PNGs — submission assets, so versioned and reviewable.
IAP_SCREENSHOTS_DIR = Path(__file__).resolve().parent / "iap_screenshots"

# Git-TRACKED parent for framed App Store screenshots; each capture run overwrites a `<device>/` subdir (stable filenames) so git history, not a timestamped dir name, records when a set changed.
APP_SCREENSHOTS_DIR = Path(__file__).resolve().parent / "app_screenshots"

# Git-TRACKED parent for App Preview videos, same `<device>/` layout as the screenshots — the submitted .mp4 is a review asset like any other and must be reviewable in the repo, not left ephemeral under ios/build/.
APP_PREVIEWS_DIR = Path(__file__).resolve().parent / "app_previews"
