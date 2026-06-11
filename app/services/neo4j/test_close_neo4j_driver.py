from typing import Any

import pytest

from app.services.neo4j import get_neo4j_driver as get_neo4j_driver_mod
from app.services.neo4j._driver_state import driver_state
from app.services.neo4j.close_neo4j_driver import close_neo4j_driver
from app.services.neo4j.get_neo4j_driver import get_neo4j_driver


async def test_close_driver_resets(monkeypatch: pytest.MonkeyPatch) -> None:
    closed: list[bool] = []

    class _FakeDriver:
        async def close(self) -> None:
            closed.append(True)

    def _factory(*_a: Any, **_k: Any) -> _FakeDriver:
        return _FakeDriver()

    monkeypatch.setattr(get_neo4j_driver_mod.AsyncGraphDatabase, "driver", _factory)
    driver_state.driver = None
    get_neo4j_driver()
    await close_neo4j_driver()
    assert closed == [True]
    assert driver_state.driver is None
