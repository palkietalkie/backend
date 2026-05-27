from app.services.neo4j import get_driver as _get_driver_module


async def close_driver() -> None:
    if _get_driver_module._driver is not None:
        await _get_driver_module._driver.close()
        _get_driver_module._driver = None
