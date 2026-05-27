from neo4j import AsyncDriver, AsyncSession


def open_session(driver: AsyncDriver) -> AsyncSession:
    """Centralized wrapper for ``driver.session()``.

    The neo4j 6.x runtime exposes ``session(**config)`` with ``Unknown``-typed kwargs (pyright doesn't follow the lib's TYPE_CHECKING re-export through ``_typing``). A local stub at ``stubs/neo4j/__init__.pyi`` types this method as ``() -> AsyncSession``, and routing every call through this single function keeps the stub's surface minimal.
    """
    return driver.session()
