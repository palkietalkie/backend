"""The `Listing` record — one locale's App Store Connect listing copy.

Pure type. The copy itself is the SSoT in `app/asc/metadata/<locale>/*.txt` (fastlane `deliver` folder layout: one file per field) and is loaded by `load_listings.py`. Never re-type the copy into docs (`ios/APPSTORE.md`); that copy is exactly what drifts.

Two ASC resources own different fields: name + subtitle + privacyPolicyUrl live on `appInfoLocalizations` (the App Store product header); description + keywords + promotionalText + supportUrl + marketingUrl live on `appStoreVersionLocalizations` (per-version; promotionalText updates without a new build).

Apple field limits, enforced by review not the pusher: subtitle 30 chars, description 4000, keywords 100, promotionalText 170."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Listing:
    locale: str

    name: str
    """App name — appInfoLocalizations.name."""

    subtitle: str
    """One-line tagline under the name — appInfoLocalizations.subtitle (30 char limit)."""

    privacy_policy_url: str
    """Privacy policy URL — appInfoLocalizations.privacyPolicyUrl. Required for review; any path works (Apple only checks reachability)."""

    description: str
    """Long-form product copy — appStoreVersionLocalizations.description."""

    keywords: str
    """Search keywords, comma-separated — appStoreVersionLocalizations.keywords (100 char limit)."""

    promotional_text: str
    """Above-the-fold promo blurb — appStoreVersionLocalizations.promotionalText (170 char limit)."""

    support_url: str
    """appStoreVersionLocalizations.supportUrl."""

    marketing_url: str
    """appStoreVersionLocalizations.marketingUrl."""
