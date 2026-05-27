import asyncpg

from app.config import get_settings
from app.services.neon import _pool_state
from app.services.neon.init_connection import init_connection
from app.services.neon.normalize_url import normalize_url


async def get_pool() -> asyncpg.Pool:
    # Lazy on first call so importing app.main doesn't dial the DB when secrets are missing (CI without prod env).
    if _pool_state.POOL is None:
        settings = get_settings()
        _pool_state.POOL = await asyncpg.create_pool(
            normalize_url(settings.neon_database_url),
            min_size=1,
            max_size=10,
            init=init_connection,
        )
    assert _pool_state.POOL is not None
    return _pool_state.POOL
