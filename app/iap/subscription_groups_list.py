"""The two Palkie Talkie subscription groups.

A subscription group is the set of mutually-exclusive plans a user picks among (monthly vs yearly of one tier). Apple requires at least one group localization (a customer-facing display name) or every subscription inside stays MISSING_METADATA and cannot be submitted.

Group reference names match `group_reference` on each `Subscription` in `subscriptions_list.py`. The pusher (`scripts/asc/set_subscription_group_metadata.py`) resolves each to its ASC id by reference name, so no numeric id is duplicated here."""

from __future__ import annotations

from app.iap.subscription import GroupLocalization, SubscriptionGroup

SUBSCRIPTION_GROUPS: tuple[SubscriptionGroup, ...] = (
    SubscriptionGroup(
        group_reference="palkietalkie.individual",
        localizations=(GroupLocalization(locale="en-US", name="Palkie Talkie Individual"),),
    ),
    SubscriptionGroup(
        group_reference="palkietalkie.family",
        localizations=(GroupLocalization(locale="en-US", name="Palkie Talkie Family"),),
    ),
)
