"""Load App Store listing copy from the `metadata/<locale>/*.txt` SSoT folder.

The folder follows fastlane `deliver`'s layout (one file per field) so the copy is atomic, git-diffable, human-editable, and a zero-migration path to `fastlane deliver` later. We read it from Python rather than adding the fastlane gem because our App Store Connect automation (subscriptions, pricing, screenshots) is Python and fastlane cannot manage in-app purchases — one toolchain, not two.

Each file maps to a `Listing` field by name (fastlane's filenames). A trailing newline is stripped so values match what ASC stores."""

from __future__ import annotations

from pathlib import Path

from app.asc.listing import Listing

METADATA_DIR = Path(__file__).resolve().parent / "metadata"

# fastlane deliver filename -> Listing field name.
_FIELD_FILES = {
    "name": "name.txt",
    "subtitle": "subtitle.txt",
    "privacy_policy_url": "privacy_url.txt",
    "description": "description.txt",
    "keywords": "keywords.txt",
    "promotional_text": "promotional_text.txt",
    "support_url": "support_url.txt",
    "marketing_url": "marketing_url.txt",
}


def load_listings() -> tuple[Listing, ...]:
    """Build a `Listing` per locale subdirectory under `metadata/`."""
    listings: list[Listing] = []
    for locale_dir in sorted(p for p in METADATA_DIR.iterdir() if p.is_dir()):
        fields = {
            field: (locale_dir / filename).read_text(encoding="utf-8").rstrip("\n")
            for field, filename in _FIELD_FILES.items()
        }
        listings.append(Listing(locale=locale_dir.name, **fields))
    return tuple(listings)
