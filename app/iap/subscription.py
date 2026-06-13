"""Canonical subscription product metadata.

Single source of truth for everything the four auto-renewing subscriptions need across the codebase: StoreKit (iOS) product ids, ASC API resource ids (management scripts), Stripe price ids (web checkout), display/marketing copy (en-US — extend `Locale.name`/`description` per added locale), screenshot bullets, USD price targets.

Anything that reads or writes subscription state — iOS Swift constants, backend ASN/Stripe webhook handlers, ASC management scripts, the website checkout — should look up products through this file via codegen. Never re-declare an id, price, or string anywhere else."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Localization:
    locale: str
    name: str
    description: str


@dataclass(frozen=True)
class StripePriceIds:
    sandbox: str
    live: str


@dataclass(frozen=True)
class GroupLocalization:
    locale: str
    name: str
    """Customer-facing group display name shown in the iOS Settings -> Subscriptions screen."""


@dataclass(frozen=True)
class SubscriptionGroup:
    group_reference: str
    """ASC `referenceName` of the group — the pusher discovers the ASC id by matching this."""

    localizations: tuple[GroupLocalization, ...]
    """At least one (en-US) is required or every subscription in the group stays MISSING_METADATA."""


@dataclass(frozen=True)
class Subscription:
    asc_id: str
    """Apple's ASC API resource id (numeric string). Used by `scripts/asc/*` only."""

    product_id: str
    """iOS bundle-id-style product id. What StoreKit `Product.products(for:)` requests."""

    asc_reference_name: str
    """ASC internal "Reference Name" — visible only in App Store Connect, not to users."""

    group_reference: str
    """Reference name of the `subscriptionGroup` the product belongs to."""

    tier: str
    """Display tier — "Individual" | "Family"."""

    cycle: str
    """Display cycle — "Monthly" | "Yearly"."""

    family_shareable: bool
    """If True, the subscription is shareable with the family-share group on the buyer's Apple ID."""

    subscription_period: str
    """Apple's `subscriptionPeriod` enum value — `ONE_MONTH` | `ONE_YEAR`."""

    target_usd_price: str
    """Target USD customer price (no symbol). Used to look up Apple's subscription price point."""

    stripe_price: StripePriceIds
    """Stripe price ids — sandbox for dev, live for prd. Web checkout reads the right one based on APP_ENV."""

    localizations: tuple[Localization, ...]
    """Display name + description per locale. en-US is required by Apple for submission."""

    screenshot_bullets: tuple[str, ...]
    """3-4 short bullet phrases the placeholder screenshot generator paints on the PNG."""
