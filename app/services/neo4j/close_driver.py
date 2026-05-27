from app.services.neo4j.driver_state import driver_state


async def close_driver() -> None:
    if driver_state.driver is not None:
        await driver_state.driver.close()
        driver_state.driver = None
