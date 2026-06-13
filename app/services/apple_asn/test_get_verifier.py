"""Tests for get_verifier — caches across calls, raises when SDK absent."""

from collections.abc import Iterator
from typing import Any

import pytest

from app.apple_identifiers import APPLE_BUNDLE_ID
from app.services.apple_asn import _state
from app.services.apple_asn import get_verifier as mod
from app.services.apple_asn.exceptions import AppleLibraryMissingError
from app.services.apple_asn.reset_caches import reset_caches


@pytest.fixture(autouse=True)
def reset_state() -> Iterator[None]:
    reset_caches()
    yield
    reset_caches()


async def test_get_verifier_raises_when_sdk_absent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "APPLE_LIB_AVAILABLE", False)
    with pytest.raises(AppleLibraryMissingError):
        await mod.get_verifier()


async def test_get_verifier_caches_after_first_call(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mod, "APPLE_LIB_AVAILABLE", True)

    async def _fake_roots() -> list[bytes]:
        return [b"root"]

    monkeypatch.setattr(mod, "load_apple_root_certs", _fake_roots)

    constructed: list[dict[str, Any]] = []

    class _FakeVerifier:
        def __init__(self, **kwargs: Any) -> None:
            constructed.append(kwargs)

    monkeypatch.setattr(mod, "SignedDataVerifier", _FakeVerifier)

    first = await mod.get_verifier()
    second = await mod.get_verifier()
    assert first is second
    assert len(constructed) == 1
    assert _state.VERIFIER_CACHE is first
    # Verifier is built against the bundle-id constant, not a Settings field.
    assert constructed[0]["bundle_id"] == APPLE_BUNDLE_ID
