from collections.abc import AsyncIterator

from app.services.neon.db_conn import DBConn
from app.services.neon.get_pool import get_pool


async def get_db() -> AsyncIterator[DBConn]:
    """FastAPI dependency yielding a connection from the pool.

    The connection is returned to the pool on context exit. Each request gets its own
    connection; there is no implicit transaction — callers use ``async with conn.transaction():``
    when they need atomicity.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
