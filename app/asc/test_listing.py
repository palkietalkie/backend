"""Lock the Listing dataclass shape — `scripts/asc/set_app_metadata.py` and `app/asc/load_listings.py` read these fields by name, so a rename silently breaks the ASC metadata push."""

import dataclasses

import pytest

from app.asc.listing import Listing


def _sample() -> Listing:
    return Listing(
        locale="en-US",
        name="N",
        subtitle="S",
        description="D",
        keywords="k",
        promotional_text="p",
        support_url="https://x",
        marketing_url="https://y",
    )


def test_listing_is_frozen() -> None:
    listing = _sample()
    # Field name via a variable: a literal setattr trips ruff B010, and a direct frozen-field assignment is a type error we are not allowed to silence.
    field = "name"
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(listing, field, "x")


def test_listing_attributes_pusher_depends_on() -> None:
    expected = {
        "locale",
        "name",
        "subtitle",
        "description",
        "keywords",
        "promotional_text",
        "support_url",
        "marketing_url",
    }
    assert set(Listing.__dataclass_fields__.keys()) == expected
