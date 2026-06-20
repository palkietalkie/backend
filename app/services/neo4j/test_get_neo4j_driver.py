from typing import Any

import pytest

from app.config import Settings
from app.services.neo4j import get_neo4j_driver as get_neo4j_driver_mod
from app.services.neo4j._driver_state import driver_state
from app.services.neo4j.get_neo4j_driver import get_neo4j_driver


class _FakeDriver:
    async def close(self) -> None:
        pass


def test_get_neo4j_driver_is_singleton(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, tuple[str, str]]] = []

    def _fake_driver_factory(uri: str, auth: tuple[str, str], **_config: Any) -> _FakeDriver:
        calls.append((uri, auth))
        return _FakeDriver()

    monkeypatch.setattr(get_neo4j_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory)
    driver_state.driver = None

    a = get_neo4j_driver()
    b = get_neo4j_driver()
    assert a is b
    assert len(calls) == 1


def test_get_neo4j_driver_uses_configured_uri(
    monkeypatch: pytest.MonkeyPatch, settings: Settings
) -> None:
    seen: dict[str, Any] = {}

    def _fake_driver_factory(uri: str, auth: tuple[str, str], **config: Any) -> _FakeDriver:
        seen["uri"] = uri
        seen["auth"] = auth
        seen["config"] = config
        return _FakeDriver()

    monkeypatch.setattr(get_neo4j_driver_mod.AsyncGraphDatabase, "driver", _fake_driver_factory)
    driver_state.driver = None
    get_neo4j_driver()
    assert seen["uri"] == settings.neo4j_uri
    assert seen["auth"] == (settings.neo4j_user, settings.neo4j_password)
    # Pool-health config that keeps a stale AuraDB connection from blocking conversation start: liveness check before reuse, proactive recycling, and a bounded acquisition wait. Asserting they're passed locks the fix against a silent revert to the 1h-lifetime / no-liveness defaults.
    assert seen["config"]["liveness_check_timeout"] == 30
    assert seen["config"]["max_connection_lifetime"] == 300
    assert seen["config"]["connection_acquisition_timeout"] == 10
