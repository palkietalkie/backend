from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings

# Shared singleton state — close_driver.py mutates this too.
_driver: AsyncDriver | None = None


def get_driver() -> AsyncDriver:
    global _driver
    if _driver is None:
        s = get_settings()
        _driver = AsyncGraphDatabase.driver(s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password))
    return _driver
