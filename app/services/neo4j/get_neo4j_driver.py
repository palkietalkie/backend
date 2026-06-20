from neo4j import AsyncDriver, AsyncGraphDatabase

from app.config import get_settings
from app.services.neo4j._driver_state import driver_state


def get_neo4j_driver() -> AsyncDriver:
    if driver_state.driver is None:
        s = get_settings()
        driver_state.driver = AsyncGraphDatabase.driver(
            s.neo4j_uri,
            auth=(s.neo4j_user, s.neo4j_password),
            # AuraDB's load balancer closes idle connections server-side well before the driver's 1h default max_connection_lifetime, so the pool hands out a connection Aura already killed and the read blocks on a dead socket until the OS timeout (~60s) — the source of the conversation-start hangs. liveness_check_timeout pings any connection idle past this before reusing it; the shorter lifetime recycles them proactively; connection_acquisition_timeout caps the wait so a degraded pool fails fast (the caller's @fallback timeout is the outer backstop).
            liveness_check_timeout=30,
            max_connection_lifetime=300,
            connection_acquisition_timeout=10,
        )
    return driver_state.driver
