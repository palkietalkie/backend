from dataclasses import dataclass

import asyncpg

from app.config import get_settings
from app.services.neon.normalize_neon_url import normalize_neon_url
from app.services.neon.register_json_codecs import register_json_codecs


@dataclass
class _PoolState:
    pool: asyncpg.Pool | None = None


# Single consumer (this file), so the holder lives inline — same shape as get_pinecone_client. A separate state module is only warranted when a getter AND a teardown share the handle (cf. neo4j's _driver_state).
_state = _PoolState()


async def get_neon_pool() -> asyncpg.Pool:
    # A pool, not per-request connect: each new Neon connection is a TCP+TLS+auth round trip (tens of ms over the network from Fly sjc), and Neon caps concurrent connections — connecting per request would tax every endpoint and blow that cap under load.
    # asyncpg connections also can't be shared across concurrent tasks; the pool hands each in-flight request its own warm connection and bounds total concurrency to max_size.
    # Lazy on first call so importing app.main doesn't dial the DB when secrets are missing (CI without prod env).
    if _state.pool is None:
        settings = get_settings()
        _state.pool = await asyncpg.create_pool(
            normalize_neon_url(settings.neon_database_url),
            min_size=1,
            max_size=10,
            init=register_json_codecs,
        )
    assert _state.pool is not None
    return _state.pool
