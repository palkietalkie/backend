"""Lock the metadata-folder loader: load_listings() reconstructs a Listing per locale from `app/asc/metadata/<locale>/*.txt`, with the trailing newline stripped (ASC stores no trailing newline, so the idempotent pusher would otherwise PATCH forever)."""

from app.asc.load_listings import load_listings

# Apple field limits the pusher relies on the SSoT to respect (it does not truncate).
APPLE_LIMITS = {"subtitle": 30, "keywords": 100, "promotional_text": 170}


def test_en_us_locale_loads() -> None:
    assert "en-US" in {listing.locale for listing in load_listings()}


def test_all_fields_non_empty() -> None:
    for listing in load_listings():
        for field in ("name", "subtitle", "description", "keywords", "promotional_text"):
            assert getattr(listing, field), f"{listing.locale} {field} is empty"


def test_no_trailing_newline() -> None:
    # The loader rstrips "\n"; a regression here would make the idempotency diff never settle.
    for listing in load_listings():
        for field in (
            "name",
            "subtitle",
            "description",
            "keywords",
            "promotional_text",
            "support_url",
            "marketing_url",
        ):
            value = getattr(listing, field)
            assert not value.endswith("\n"), f"{listing.locale} {field} has a trailing newline"


def test_urls_are_https() -> None:
    for listing in load_listings():
        assert listing.support_url.startswith("https://")
        assert listing.marketing_url.startswith("https://")


def test_fields_within_apple_limits() -> None:
    for listing in load_listings():
        for field, limit in APPLE_LIMITS.items():
            value = getattr(listing, field)
            assert len(value) <= limit, f"{listing.locale} {field} is {len(value)} chars (>{limit})"
