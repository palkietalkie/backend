from app.services.neo4j import get_driver as get_driver_mod
from app.services.neo4j.close_driver import close_driver
from app.services.neo4j.get_driver import get_driver


async def test_close_driver_resets(monkeypatch) -> None:
    closed = []

    class _FakeDriver:
        async def close(self) -> None:
            closed.append(True)

    monkeypatch.setattr(
        get_driver_mod.AsyncGraphDatabase, "driver", lambda *_a, **_k: _FakeDriver()
    )
    monkeypatch.setattr(get_driver_mod, "_driver", None)
    get_driver()
    await close_driver()
    assert closed == [True]
    assert get_driver_mod._driver is None
