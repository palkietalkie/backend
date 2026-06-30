"""App Privacy ("nutrition label") declaration — the SSoT for what Palkie Talkie collects.

Unlike listing copy, this CANNOT be pushed via the App Store Connect API: Apple ships no `appDataUsages` resource (every privacy endpoint 404s as "does not exist"), and fastlane can't set it either. So the one-time entry is manual in the ASC web dashboard (App Store → App Privacy). This module is still the SSoT so the declaration is version-controlled and reviewable; `scripts/asc/print_app_privacy.py` renders it as a click-by-click checklist.

Each record is one row of Apple's questionnaire: a data type, whether it's linked to the user's identity, whether it's used to track across other companies' apps/sites, and the collection purposes. Labels are Apple's exact questionnaire strings so the dashboard entry is a transcription.

Decisions baked in (the non-obvious ones):

Transcripts + Audio carry a Product Personalization purpose because memory/persona recall is the product; the "product improvement / model training" consent toggle maps to Apple's "Other Purposes" (Apple has no model-training purpose).

Nothing is used for tracking: there is no third-party ad SDK and no cross-app identifier sharing."""

from __future__ import annotations

from dataclasses import dataclass

# Apple's exact purpose labels (App Store Connect → App Privacy questionnaire).
APP_FUNCTIONALITY = "App Functionality"
ANALYTICS = "Analytics"
PRODUCT_PERSONALIZATION = "Product Personalization"
OTHER_PURPOSES = "Other Purposes"


@dataclass(frozen=True)
class CollectedData:
    category: str
    """Apple data category header, e.g. "Contact Info", "User Content"."""

    data_type: str
    """Apple data type within the category, e.g. "Email Address", "Audio Data"."""

    linked_to_identity: bool
    """Whether the data is tied to the user's account/identity."""

    used_for_tracking: bool
    """Whether the data tracks the user across other companies' apps and websites."""

    purposes: tuple[str, ...]
    """Why it's collected — Apple questionnaire purpose labels."""


APP_PRIVACY: tuple[CollectedData, ...] = (
    CollectedData(
        category="Contact Info",
        data_type="Email Address",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY,),
    ),
    CollectedData(
        category="Contact Info",
        data_type="Name",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY, PRODUCT_PERSONALIZATION),
    ),
    CollectedData(
        category="User Content",
        data_type="Audio Data",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY, PRODUCT_PERSONALIZATION, OTHER_PURPOSES),
    ),
    CollectedData(
        category="User Content",
        data_type="Other User Content",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY, PRODUCT_PERSONALIZATION, OTHER_PURPOSES),
    ),
    CollectedData(
        category="Identifiers",
        data_type="User ID",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY,),
    ),
    CollectedData(
        category="Usage Data",
        data_type="Product Interaction",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(ANALYTICS, APP_FUNCTIONALITY),
    ),
    CollectedData(
        category="Diagnostics",
        data_type="Performance Data",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(ANALYTICS, APP_FUNCTIONALITY),
    ),
    CollectedData(
        category="Other Data",
        data_type="Other Data Types",
        linked_to_identity=True,
        used_for_tracking=False,
        purposes=(APP_FUNCTIONALITY, PRODUCT_PERSONALIZATION),
    ),
)
