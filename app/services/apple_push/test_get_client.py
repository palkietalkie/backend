"""get_client builds the APNs client with our bundle id as the push topic, and caches it."""

from typing import Any

import pytest

from app.apple_identifiers import APPLE_BUNDLE_ID
from app.services.apple_push import get_client as mod


def test_get_client_uses_bundle_id_as_topic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_client", None)
    captured: list[dict[str, Any]] = []

    class _FakeAPNs:
        def __init__(self, **kwargs: Any) -> None:
            captured.append(kwargs)

    monkeypatch.setattr(mod, "APNs", _FakeAPNs)
    mod.get_client()
    assert captured[0]["topic"] == APPLE_BUNDLE_ID


def test_get_client_caches_across_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "_client", None)

    class _FakeAPNs:
        def __init__(self, **kwargs: Any) -> None: ...

    monkeypatch.setattr(mod, "APNs", _FakeAPNs)
    assert mod.get_client() is mod.get_client()
