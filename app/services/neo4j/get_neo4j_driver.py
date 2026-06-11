from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings
from app.services.neo4j._driver_state import driver_state


def get_neo4j_driver() -> AsyncDriver:
    if driver_state.driver is None:
        s = get_settings()
        driver_state.driver = AsyncGraphDatabase.driver(
            s.neo4j_uri, auth=(s.neo4j_user, s.neo4j_password)
        )
    return driver_state.driver
