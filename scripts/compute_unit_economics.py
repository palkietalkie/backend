"""Unit economics for the OpenAI Realtime voice loop, from real usage + real billed cost.

Run: cd backend && uv run python -m scripts.compute_unit_economics [--env prd|dev|all]

Minutes come from conversation_sessions.duration_seconds (we own them). Cost is the ACTUAL OpenAI
org spend over the same window, pulled via the admin Costs API, so the blended $/min is measured,
not guessed. OpenAI billing is account-wide (one org spans prd + dev + ad-hoc testing), so the cost
figure is the whole account regardless of --env; the per-env split is usage-minutes only.
"""

import argparse
import asyncio
import datetime as dt

import asyncpg

from app.iap.subscriptions_list import SUBSCRIPTIONS
from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from scripts.openai.fetch_openai_cost import fetch_openai_cost
from scripts.read_neon_url import read_neon_url

# Individual Monthly price is owned by the IAP product list (SSoT); don't restate the number here.
INDIVIDUAL_MONTHLY_USD = float(
    next(
        s.target_usd_price
        for s in SUBSCRIPTIONS
        if s.product_id == "com.palkietalkie.individual.monthly"
    )
)
APPLE_CUT_YEAR1 = 0.30  # App Store takes 30% in year 1, 15% after.
WEEKS_PER_MONTH = 52 / 12


async def _aggregate(conn: asyncpg.Connection) -> dict[str, float]:
    row = await conn.fetchrow(
        """SELECT
             count(*) FILTER (WHERE ended_at IS NOT NULL)               AS ended,
             count(*) FILTER (WHERE ended_at IS NULL)                   AS still_open,
             count(DISTINCT user_id)                                    AS users,
             COALESCE(sum(duration_seconds) FILTER (WHERE ended_at IS NOT NULL), 0) AS secs,
             min(started_at)::date AS first_day,
             max(started_at)::date AS last_day
           FROM conversation_sessions"""
    )
    assert row is not None
    return dict(row)


async def _aggregate_env(env: str) -> dict[str, float]:
    conn = await asyncpg.connect(read_neon_url(env))
    try:
        return await _aggregate(conn)
    finally:
        await conn.close()


def _line(label: str, value: str) -> str:
    return f"  {label:<36} {value}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", choices=["prd", "dev", "all"], default="all")
    args = parser.parse_args()
    envs = ["prd", "dev"] if args.env == "all" else [args.env]

    async def run() -> None:
        per_env = {env: await _aggregate_env(env) for env in envs}

        secs = sum(a["secs"] for a in per_env.values())
        ended = sum(a["ended"] for a in per_env.values())
        still_open = sum(a["still_open"] for a in per_env.values())
        users = (
            int(sum(a["users"] for a in per_env.values())) or 1
        )  # upper bound (envs can overlap)
        first_day = min(a["first_day"] for a in per_env.values())
        last_day = max(a["last_day"] for a in per_env.values())
        minutes = secs / 60.0

        first_date = dt.date.fromisoformat(str(first_day))
        actual_cost, by_item = fetch_openai_cost(first_date)
        # Blended all-in inference cost per conversation-minute: every OpenAI line item (realtime audio/text both tiers + transcription) over the measured minutes.
        # The numerator also covers the still-open sessions we couldn't measure, so this rate is a slight over-estimate (safe).
        rate = actual_cost / minutes if minutes else 0.0

        net_per_paid = INDIVIDUAL_MONTHLY_USD * (1 - APPLE_CUT_YEAR1)
        covered_min_month = net_per_paid / rate if rate else 0.0

        print(f"\nPalkie Talkie — voice unit economics ({'+'.join(envs)})")
        print(f"  window {first_day} → {last_day}   (OpenAI cost is account-wide)\n")

        if len(per_env) > 1:
            print("Usage by environment:")
            for env, a in per_env.items():
                print(
                    _line(
                        env,
                        f"{a['secs'] / 60:.1f} min, {int(a['users'])} users, "
                        f"{int(a['ended'])} ended / {int(a['still_open'])} open",
                    )
                )
            print()

        print("Usage (measured = ended sessions, combined):")
        print(
            _line(
                "sessions ended / still open",
                f"{int(ended)} / {int(still_open)} (open = unmeasured)",
            )
        )
        print(_line("distinct users (upper bound)", str(users)))
        print(_line("total minutes", f"{minutes:.1f}"))
        print(_line("avg minutes / user", f"{minutes / users:.1f}"))

        print("\nActual OpenAI cost (admin Costs API, account-wide):")
        print(_line("total spent this window", f"${actual_cost:.2f}"))
        print(_line("blended rate", f"${rate:.3f}/min  (= ${rate * 60:.2f}/hr)"))
        print("  top line items:")
        for item, val in sorted(by_item.items(), key=lambda x: -x[1])[:5]:
            print(_line(f"    {item}", f"${val:.2f}"))

        print(f"\nPaid tier coverage (Individual ${INDIVIDUAL_MONTHLY_USD:.2f}/mo):")
        print(_line("year-1 net after 30% Apple", f"${net_per_paid:.2f}"))
        print(
            _line(
                "covers at blended rate",
                f"{covered_min_month:.0f} min/mo (~{covered_min_month / 30:.1f} min/day) before margin breaks",
            )
        )

        # Monthly cost is governed by the WEEKLY cap, not the daily one, since the daily cap only paces usage inside a week.
        # To actually grant more talk time you raise the weekly cap (and the daily with it), and cost scales with the weekly number.
        print(f"\nFree-tier cost per user, by WEEKLY cap (at ${rate:.3f}/min):")
        for weekly in (FREE_MINUTES_PER_WEEK, 45, 60, 90):
            monthly = weekly * rate * WEEKS_PER_MONTH
            tag = "  ← current" if weekly == FREE_MINUTES_PER_WEEK else ""
            print(
                _line(f"{weekly} min/week", f"${weekly * rate:.2f}/wk = ${monthly:.2f}/mo max{tag}")
            )
        print(
            f"\n  Current daily cap {FREE_MINUTES_PER_DAY} min just paces the weekly {FREE_MINUTES_PER_WEEK}. "
            "Raising the daily limit grants more only if the weekly rises too; that's the cost lever.\n"
        )

    asyncio.run(run())


if __name__ == "__main__":
    main()
