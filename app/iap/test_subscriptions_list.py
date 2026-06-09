"""Lock in the four auto-renewing subscriptions and the invariants that downstream scripts (ASC creator/localizer, Stripe webhook, iOS StoreKit) rely on: stable product ids, every product has en-US localization, prices match the published table."""

from app.iap.subscriptions_list import SUBSCRIPTIONS


def test_exactly_four_subscriptions() -> None:
    assert len(SUBSCRIPTIONS) == 4


def test_product_ids_match_published_set() -> None:
    expected = {
        "com.palkietalkie.individual.monthly",
        "com.palkietalkie.individual.yearly",
        "com.palkietalkie.family.monthly",
        "com.palkietalkie.family.yearly",
    }
    assert {s.product_id for s in SUBSCRIPTIONS} == expected


def test_every_product_has_en_us_localization() -> None:
    for s in SUBSCRIPTIONS:
        assert any(loc.locale == "en-US" for loc in s.localizations), (
            f"{s.product_id} missing en-US localization (Apple requires it for submission)"
        )


def test_tier_and_cycle_values_are_canonical() -> None:
    for s in SUBSCRIPTIONS:
        assert s.tier in {"Individual", "Family"}, f"{s.product_id} bad tier {s.tier!r}"
        assert s.cycle in {"Monthly", "Yearly"}, f"{s.product_id} bad cycle {s.cycle!r}"


def test_subscription_period_matches_cycle() -> None:
    for s in SUBSCRIPTIONS:
        expected = "ONE_MONTH" if s.cycle == "Monthly" else "ONE_YEAR"
        assert s.subscription_period == expected, (
            f"{s.product_id} cycle={s.cycle} but period={s.subscription_period!r}"
        )


def test_family_shareable_only_set_on_family_tier() -> None:
    for s in SUBSCRIPTIONS:
        if s.tier == "Family":
            assert s.family_shareable, f"{s.product_id} is Family but not shareable"
        else:
            assert not s.family_shareable, f"{s.product_id} is {s.tier} but marked shareable"


def test_target_usd_prices_match_published_table() -> None:
    # Per /CLAUDE.md Business Model: Individual $17.99/$83.99, Family $19.99/$112.99.
    by_pid = {s.product_id: s.target_usd_price for s in SUBSCRIPTIONS}
    assert by_pid["com.palkietalkie.individual.monthly"] == "17.99"
    assert by_pid["com.palkietalkie.individual.yearly"] == "83.99"
    assert by_pid["com.palkietalkie.family.monthly"] == "19.99"
    assert by_pid["com.palkietalkie.family.yearly"] == "112.99"


def test_every_product_has_screenshot_bullets() -> None:
    for s in SUBSCRIPTIONS:
        assert len(s.screenshot_bullets) > 0, f"{s.product_id} missing screenshot bullets"
