"""Shared module-level singleton for the asyncpg pool. get_pool / reset_pool mutate it."""

import asyncpg

POOL: asyncpg.Pool | None = None
