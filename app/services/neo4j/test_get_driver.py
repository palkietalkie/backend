from typing import Any

import pytest

from app.config import Settings
from app.services.neo4j import get_driver as get_driver_mod
from app.services.neo4j.driver_state import driver_state
from app.services.neo4j.get_driver import get_driver


class _FakeDriver:
    async def close(self) -> None:
        pass


def test_get_driver_is_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[str, str]]] = []

    def _fake_driver_factory(uri: str, auth: tuple[str, str]) -> _FakeDriver:
        calls.append((uri, auth))
        return _FakeDriver()

    monkeypatch.setattr(get_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory)
    driver_state.driver = None

    a = get_driver()
    b = get_driver()
    assert a is b
    assert len(calls) == 1


def test_get_driver_uses_configured_uri(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    seen: dict[str, Any] = {}

    def _fake_driver_factory(uri: str, auth: tuple[str, str]) -> _FakeDriver:
        seen["uri"] = uri
        seen["auth"] = auth
        return _FakeDriver()

    monkeypatch.setattr(get_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory)
    driver_state.driver = None
    get_driver()
    assert seen["uri"] == settings.neo4j_uri
    assert seen["auth"] == (settings.neo4j_user, settings.neo4j_password)
