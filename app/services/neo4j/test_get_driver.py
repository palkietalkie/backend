from typing import Any

from app.services.neo4j import get_driver as get_driver_mod
from app.services.neo4j.get_driver import get_driver


def test_get_driver_is_singleton(monkeypatch) -> None:
    calls = []

    class _FakeDriver:
        async def close(self) -> None:
            pass

    def _fake_driver_factory(uri: str, auth: tuple[str, str]) -> _FakeDriver:
        calls.append((uri, auth))
        return _FakeDriver()

    monkeypatch.setattr(
        get_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory
    )
    monkeypatch.setattr(get_driver_mod, "_driver", None)

    a = get_driver()
    b = get_driver()
    assert a is b
    assert len(calls) == 1


def test_get_driver_uses_configured_uri(monkeypatch, settings) -> None:
    seen: dict[str, Any] = {}

    class _FakeDriver:
        async def close(self) -> None:
            pass

    def _fake_driver_factory(uri: str, auth: tuple[str, str]) -> _FakeDriver:
        seen["uri"] = uri
        seen["auth"] = auth
        return _FakeDriver()

    monkeypatch.setattr(
        get_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory
    )
    monkeypatch.setattr(get_driver_mod, "_driver", None)
    get_driver()
    assert seen["uri"] == settings.neo4j_uri
    assert seen["auth"] == (settings.neo4j_user, settings.neo4j_password)
