#!/usr/bin/env python3
"""Merge Wes's scattered accounts (dev + prd) into the one designated prd Apple account, without duplicating data.

Wes signs in across dev/prd with Google + Apple, so his conversation history, stats, and custom personas are split across several user rows in two separate Neon databases; this consolidates them into the prd Apple account so the data (and the personalization it drives) is whole. The per-table mechanics live in count_user_data / merge_same_db / merge_cross_db; this file is just the orchestrator: which accounts, in what order, dry-run vs apply.

Auth-scoped rows (device_tokens, calendar_tokens) are intentionally NOT merged: they're per-device / per-oauth-connection, not personal data. Dry-run by default; --execute applies, each source inside its own target-DB transaction so a failure rolls that source back cleanly.

Dry-run: cd backend && uv run python -m scripts.merge_user_data

Apply: cd backend && uv run python -m scripts.merge_user_data --execute
"""

import argparse
import asyncio
from dataclasses import dataclass

import asyncpg

from scripts.count_user_data import count_user_data
from scripts.merge_cross_db import merge_cross_db
from scripts.merge_same_db import merge_same_db
from scripts.read_neon_url import read_neon_url

# Hardcoded (not a CLI arg) so a typo can never point the merge at the wrong account. prd Apple account, hnishio0105@gmail.com.
TARGET_PRD_USER_ID = "1fd8feb1-1342-47b3-8856-a02f5e78dde5"

# table -> (natural key column, recency timestamp column) for the summed aggregates. Owned here and passed in, so the merge functions stay pure.
AGG_TABLES = {
    "word_freq": ("lemma", "last_used_at"),
    "phrase_freq": ("phrase", "last_used_at"),
}


@dataclass(frozen=True)
class Source:
    env: str  # "dev" | "prd"
    user_id: str
    label: str


SOURCES = [
    Source("prd", "68cd46e4-020f-4df4-92ea-4aec3aeb7e0c", "prd Google (wesnishio@gmail.com)"),
    Source("dev", "f7a45bcb-b26d-4b7d-bc99-8b66bb753601", "dev Google (wesnishio@gmail.com)"),
    Source("dev", "30ae3d45-db06-4006-9f9c-b363bac311c0", "dev Apple (hnishio0105@gmail.com)"),
]


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", help="apply the merge (default: dry-run)")
    args = parser.parse_args()

    prd = await asyncpg.connect(read_neon_url("prd"))
    dev = await asyncpg.connect(read_neon_url("dev"))
    try:
        print(
            f"TARGET prd {TARGET_PRD_USER_ID} BEFORE: {await count_user_data(prd, TARGET_PRD_USER_ID)}"
        )
        for s in SOURCES:
            src_conn = prd if s.env == "prd" else dev
            print(
                f"\nSOURCE {s.label} [{s.env} {s.user_id}]: {await count_user_data(src_conn, s.user_id)}"
            )
            if not args.execute:
                print("  (dry-run — nothing written)")
                continue
            async with prd.transaction():
                if s.env == "prd":
                    await merge_same_db(prd, s.user_id, TARGET_PRD_USER_ID, AGG_TABLES)
                else:
                    await merge_cross_db(dev, prd, s.user_id, TARGET_PRD_USER_ID, AGG_TABLES)
            print("  merged.")
        label = "AFTER" if args.execute else "(unchanged, dry-run)"
        print(
            f"\nTARGET prd {TARGET_PRD_USER_ID} {label}: {await count_user_data(prd, TARGET_PRD_USER_ID)}"
        )
    finally:
        await prd.close()
        await dev.close()


if __name__ == "__main__":
    asyncio.run(main())
