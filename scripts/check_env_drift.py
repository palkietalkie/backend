#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Fail if .env / .env.production / fly.toml / fly.dev.toml diverge from the canonical sources.

Two disjoint key sets the running backend reads:
  * SECRETS — credentials. Canonical list: `.env.example` SECRETS section.
                Local copies: `.env`, `.env.production` SECRETS sections.
  * CONFIG  — non-secret runtime config. Canonical list: `fly.toml [env]` block.
                Per-env override: `fly.dev.toml [env]` block.

Invariants enforced:
  1. `.env` and `.env.production` SECRETS sections ⊇ `.env.example` SECRETS keys.
  2. `fly.toml [env]` and `fly.dev.toml [env]` hold the same key set (same shape, different values).
  3. No key appears in both SECRETS (a .env file) and CONFIG (a fly.toml) — they must be disjoint.

We don't talk to Fly here (no network in pre-commit); drift between local files and live Fly secrets is caught at deploy time by the workflow's secret-presence check."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SECRETS_MARKER = "SECRETS"
TOOLING_MARKER = "TOOLING"


def _read_secrets_keys(path: Path) -> set[str]:
    """Return env-var names under the SECRETS section of a .env-shaped file. Stops at the TOOLING marker so CLI helpers don't get folded in."""
    keys: set[str] = set()
    in_section = False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if SECRETS_MARKER in line and "=" not in line:
            in_section = True
            continue
        if TOOLING_MARKER in line and "=" not in line:
            in_section = False
            continue
        if not in_section or not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
        if m:
            keys.add(m.group(1))
    return keys


def _read_fly_env_keys(path: Path) -> set[str]:
    data = tomllib.loads(path.read_text())
    env = data.get("env") or {}
    return {str(k) for k in env}


def main() -> int:
    problems: list[str] = []

    canonical_secrets = _read_secrets_keys(ROOT / ".env.example")
    if not canonical_secrets:
        problems.append("  .env.example SECRETS section is empty")

    # Invariant 1: .env and .env.production must contain every canonical secret.
    for env_path in (ROOT / ".env", ROOT / ".env.production"):
        if not env_path.exists():
            continue
        local = _read_secrets_keys(env_path)
        missing = canonical_secrets - local
        if missing:
            problems.append(f"  [{env_path.name}] missing secrets: {sorted(missing)}")
        extra = local - canonical_secrets
        if extra:
            problems.append(
                f"  [{env_path.name}] extra secrets not in .env.example: {sorted(extra)}"
            )

    # Invariant 2: fly.toml [env] and fly.dev.toml [env] hold the same key set.
    fly_prd = _read_fly_env_keys(ROOT / "fly.toml") if (ROOT / "fly.toml").exists() else set()
    fly_dev = (
        _read_fly_env_keys(ROOT / "fly.dev.toml") if (ROOT / "fly.dev.toml").exists() else set()
    )
    only_prd = fly_prd - fly_dev
    only_dev = fly_dev - fly_prd
    if only_prd:
        problems.append(f"  [fly.toml] keys missing from fly.dev.toml: {sorted(only_prd)}")
    if only_dev:
        problems.append(f"  [fly.dev.toml] keys missing from fly.toml: {sorted(only_dev)}")

    # Invariant 3: secrets ∩ fly-config must be empty.
    overlap = canonical_secrets & (fly_prd | fly_dev)
    if overlap:
        problems.append(
            f"  secret/config overlap (key appears in both .env.example and a fly.toml): {sorted(overlap)}"
        )

    if problems:
        print("check_env_drift: divergence detected:", file=sys.stderr)
        for line in problems:
            print(line, file=sys.stderr)
        return 1

    print(
        f"check_env_drift: ok ({len(canonical_secrets)} canonical secrets, {len(fly_prd)} config keys)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
