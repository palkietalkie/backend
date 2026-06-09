"""The four Palkie Talkie auto-renewing subscriptions.

Add a new locale by appending a `Localization(...)` to a product's `localizations`. Add a new product by adding a `Subscription(...)` and a matching IAP in App Store Connect (the `scripts/asc/create_iap_subscriptions.py` script creates it on next run when the product id is new) plus matching Stripe prices."""

from __future__ import annotations

from app.iap.subscription import Localization, StripePriceIds, Subscription

SUBSCRIPTIONS: tuple[Subscription, ...] = (
    Subscription(
        asc_id="6777277918",
        product_id="com.palkietalkie.individual.monthly",
        asc_reference_name="Individual Monthly",
        group_reference="palkietalkie.individual",
        tier="Individual",
        cycle="Monthly",
        family_shareable=False,
        subscription_period="ONE_MONTH",
        target_usd_price="17.99",
        stripe_price=StripePriceIds(
            sandbox="price_1Tb7Wa5kJkygJqGZq0o4ssGx",
            live="price_1Tb7Wb8n3tBguXEAXS1NVSjH",
        ),
        localizations=(
            Localization(
                locale="en-US",
                name="Individual Monthly",
                description="Unlimited voice practice. 1 user.",
            ),
        ),
        screenshot_bullets=(
            "Unlimited voice practice",
            "Real-time AI tutor",
            "Memory across sessions",
        ),
    ),
    Subscription(
        asc_id="6777318996",
        product_id="com.palkietalkie.individual.yearly",
        asc_reference_name="Individual Yearly",
        group_reference="palkietalkie.individual",
        tier="Individual",
        cycle="Yearly",
        family_shareable=False,
        subscription_period="ONE_YEAR",
        target_usd_price="83.99",
        stripe_price=StripePriceIds(
            sandbox="price_1TfBGv5kJkygJqGZhvE2hah8",
            live="price_1TfBGw8n3tBguXEAPk0aTAeQ",
        ),
        localizations=(
            Localization(
                locale="en-US",
                name="Individual Yearly",
                description="Unlimited voice practice. 1 user.",
            ),
        ),
        screenshot_bullets=(
            "Unlimited voice practice",
            "Real-time AI tutor",
            "Memory across sessions",
        ),
    ),
    Subscription(
        asc_id="6777278453",
        product_id="com.palkietalkie.family.monthly",
        asc_reference_name="Family Monthly",
        group_reference="palkietalkie.family",
        tier="Family",
        cycle="Monthly",
        family_shareable=True,
        subscription_period="ONE_MONTH",
        target_usd_price="19.99",
        stripe_price=StripePriceIds(
            sandbox="price_1Tb7Wa5kJkygJqGZUxd7pwlV",
            live="price_1Tb7Wb8n3tBguXEAlICYGxRt",
        ),
        localizations=(
            Localization(
                locale="en-US",
                name="Family Monthly",
                description="Unlimited voice practice. Up to 6 users.",
            ),
        ),
        screenshot_bullets=(
            "Up to 6 users",
            "Separate profiles per user",
            "Real-time AI tutor",
        ),
    ),
    Subscription(
        asc_id="6777319257",
        product_id="com.palkietalkie.family.yearly",
        asc_reference_name="Family Yearly",
        group_reference="palkietalkie.family",
        tier="Family",
        cycle="Yearly",
        family_shareable=True,
        subscription_period="ONE_YEAR",
        target_usd_price="112.99",
        stripe_price=StripePriceIds(
            sandbox="price_1TfBGv5kJkygJqGZLMnKV36G",
            live="price_1TfBGw8n3tBguXEAITu8xy3X",
        ),
        localizations=(
            Localization(
                locale="en-US",
                name="Family Yearly",
                description="Unlimited voice practice. Up to 6 users.",
            ),
        ),
        screenshot_bullets=(
            "Up to 6 users",
            "Separate profiles per user",
            "Real-time AI tutor",
        ),
    ),
)
