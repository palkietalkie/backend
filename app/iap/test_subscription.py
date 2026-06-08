"""Type/contract assertions on the Subscription dataclass shape — iOS Swift codegen + Stripe webhook handler + ASC scripts all consume this. Catches the case where a careless rename of an attribute silently breaks one of those consumers."""

from app.iap.subscription import Localization, StripePriceIds, Subscription


def test_localization_is_frozen() -> None:
    loc = Localization(locale="en-US", name="N", description="D")
    try:
        loc.locale = "ja"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("Localization should be frozen")


def test_stripe_price_ids_is_frozen() -> None:
    p = StripePriceIds(sandbox="s", live="l")
    try:
        p.sandbox = "x"  # type: ignore[misc]
    except Exception:
        return
    raise AssertionError("StripePriceIds should be frozen")


def test_subscription_attributes_ios_codegen_depends_on() -> None:
    # Every attribute the cross-stack codegen + scripts read.
    expected = {
        "asc_id",
        "product_id",
        "asc_reference_name",
        "group_reference",
        "tier",
        "cycle",
        "family_shareable",
        "subscription_period",
        "target_usd_price",
        "stripe_price",
        "localizations",
        "screenshot_bullets",
    }
    actual = set(Subscription.__dataclass_fields__.keys())
    missing = expected - actual
    assert not missing, f"missing required Subscription attributes: {missing}"
