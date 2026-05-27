from app.services.neon import _pool_state


async def reset_pool() -> None:
    # Used by tests that swap the DB URL between sessions.
    if _pool_state.POOL is not None:
        await _pool_state.POOL.close()
        _pool_state.POOL = None
