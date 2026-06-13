"""Type/contract assertions on the Subscription dataclass shape — iOS Swift codegen + Stripe webhook handler + ASC scripts all consume this. Catches the case where a careless rename of an attribute silently breaks one of those consumers."""

import dataclasses

import pytest

from app.iap.subscription import (
    GroupLocalization,
    Localization,
    StripePriceIds,
    Subscription,
    SubscriptionGroup,
)


def _assert_frozen(instance: object, field: str) -> None:
    # Field name passed as a variable: a literal setattr trips ruff B010, and a direct frozen-field assignment is an unsilenceable type error.
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, field, "x")


def test_localization_is_frozen() -> None:
    _assert_frozen(Localization(locale="en-US", name="N", description="D"), "locale")


def test_stripe_price_ids_is_frozen() -> None:
    _assert_frozen(StripePriceIds(sandbox="s", live="l"), "sandbox")


def test_group_localization_is_frozen() -> None:
    _assert_frozen(GroupLocalization(locale="en-US", name="N"), "name")


def test_subscription_group_is_frozen() -> None:
    _assert_frozen(SubscriptionGroup(group_reference="r", localizations=()), "group_reference")


def test_subscription_group_attributes() -> None:
    assert set(SubscriptionGroup.__dataclass_fields__.keys()) == {
        "group_reference",
        "localizations",
    }
    assert set(GroupLocalization.__dataclass_fields__.keys()) == {"locale", "name"}


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
