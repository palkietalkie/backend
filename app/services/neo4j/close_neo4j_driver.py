from app.services.neo4j._driver_state import driver_state


async def close_neo4j_driver() -> None:
    if driver_state.driver is not None:
        await driver_state.driver.close()
        driver_state.driver = None
