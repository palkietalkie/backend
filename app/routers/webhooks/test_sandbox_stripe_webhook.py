"""Live integration test: Stripe Sandbox fires a real signed webhook at the deployed dev backend.

Skipped automatically unless every required env var is set, so normal ``pytest`` runs stay hermetic. Marked ``live`` so CI can opt in via ``pytest -m live`` (e.g. nightly job against ``palkietalkie-api-dev``).

Reads the same env the backend itself uses (loaded from ``backend/.env``): STRIPE_SECRET_KEY                  sandbox sk_test_... STRIPE_PRICE_INDIVIDUAL_MONTHLY    sandbox price_... DEV_NEON_DATABASE_URL              dev Neon connection string. Conftest's testcontainer fixture overwrites ``NEON_DATABASE_URL`` mid-session, so this test reads the preserved original from ``DEV_NEON_DATABASE_URL`` (stashed before the override).

Stripe Sandbox's dashboard already has the webhook destination set to ``palkietalkie-api-dev.fly.dev``, so the test doesn't configure it.

What the test does: 1. Insert a throwaway user into dev Neon with a known clerk_user_id. 2. Use Stripe Sandbox API to create a Customer + Subscription with that clerk_user_id in metadata. 3. Stripe Sandbox delivers the resulting ``customer.subscription.created`` webhook to the dev backend. 4. Poll dev DB for premium=true; assert it flips within the timeout. 5. Cleanup: cancel the subscription, delete the customer, delete the test user row."""

import asyncio
import os
import uuid

import asyncpg
import pytest

pytestmark = [pytest.mark.sandbox, pytest.mark.asyncio]

REQUIRED_ENV = (
    "STRIPE_SECRET_KEY",
    "DEV_NEON_DATABASE_URL",
)


def _require_env() -> None:
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        pytest.fail(f"live test requires env vars (set in backend/.env): {', '.join(missing)}")


async def _wait_for_premium(
    pool: asyncpg.Pool, user_id: uuid.UUID, expected: bool, timeout_s: float = 90
) -> bool:
    # Stripe webhook delivery latency is usually < 5s but can spike. Poll every 2s up to the timeout.
    deadline = asyncio.get_event_loop().time() + timeout_s
    while asyncio.get_event_loop().time() < deadline:
        async with pool.acquire() as conn:
            row = await conn.fetchrow("SELECT premium FROM users WHERE id = $1", user_id)
        if row is not None and row["premium"] is expected:
            return True
        await asyncio.sleep(2)
    return False


async def test_real_stripe_sandbox_subscription_flips_premium() -> None:
    _require_env()
    import stripe

    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    # Stripe price id comes from the canonical product list — sandbox value for this dev test.
    from app.iap.subscriptions_list import SUBSCRIPTIONS

    price_id = next(
        s.stripe_price.sandbox
        for s in SUBSCRIPTIONS
        if s.tier == "Individual" and s.cycle == "Monthly"
    )
    db_url = os.environ["DEV_NEON_DATABASE_URL"]

    user_id = uuid.uuid4()
    clerk_user_id = f"user_live_stripe_{user_id.hex[:8]}"

    pool = await asyncpg.create_pool(db_url, min_size=1, max_size=2)
    assert pool is not None
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO users (id, clerk_user_id, premium)
                   VALUES ($1, $2, FALSE)""",
                user_id,
                clerk_user_id,
            )

        # Create a sandbox customer + subscription; Stripe will fire the webhook to the dev backend.
        customer = stripe.Customer.create(
            metadata={"clerk_user_id": clerk_user_id},
            description=f"live integration test {clerk_user_id}",
        )
        # Attach a pre-made test PaymentMethod by token ID — never put raw card data on the wire. Stripe sandboxes nag if you pass `card={"number": ...}` even with their published Visa test card. `pm_card_visa` is the documented Stripe-provided PM that "always succeeds without 3DS." Other useful IDs: `pm_card_visa_chargeDeclined`, `pm_card_authenticationRequired`.
        # `attach()` returns a PaymentMethod object whose `.id` is the customer-bound `pm_1...` id. Use THAT id to set the default — Stripe used to alias the literal token "pm_card_visa" back to the attached pm id, but stopped accepting the alias on Customer.modify in recent API versions, producing "customer does not have a payment method with the ID pm_1..." even though the attach succeeded.
        attached_pm = stripe.PaymentMethod.attach("pm_card_visa", customer=customer.id)
        stripe.Customer.modify(
            customer.id, invoice_settings={"default_payment_method": attached_pm.id}
        )
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            metadata={"clerk_user_id": clerk_user_id},
        )

        try:
            flipped = await _wait_for_premium(pool, user_id, expected=True)
            assert flipped, "premium did not flip to true within 90s of sandbox subscription create"
        finally:
            stripe.Subscription.cancel(subscription.id)
            stripe.Customer.delete(customer.id)
    finally:
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        await pool.close()
