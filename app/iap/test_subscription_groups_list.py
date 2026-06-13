"""Lock the subscription groups. The invariant that broke real ASC submission: every group a subscription points at MUST have a customer-facing localization, or Apple holds every subscription in that group at MISSING_METADATA."""

from app.iap.subscription_groups_list import SUBSCRIPTION_GROUPS
from app.iap.subscriptions_list import SUBSCRIPTIONS


def test_groups_cover_every_referenced_group() -> None:
    referenced = {s.group_reference for s in SUBSCRIPTIONS}
    defined = {g.group_reference for g in SUBSCRIPTION_GROUPS}
    assert referenced == defined, f"subs reference {referenced} but groups define {defined}"


def test_every_group_has_en_us_localization() -> None:
    for g in SUBSCRIPTION_GROUPS:
        assert any(loc.locale == "en-US" for loc in g.localizations), (
            f"{g.group_reference} has no en-US localization — its subscriptions stay MISSING_METADATA"
        )


def test_group_display_names_within_apple_limit() -> None:
    for g in SUBSCRIPTION_GROUPS:
        for loc in g.localizations:
            assert 0 < len(loc.name) <= 30, (
                f"{g.group_reference} {loc.locale} name {loc.name!r} must be 1-30 chars"
            )
