"""Tests for the apple_asn root certificate loader (httpx mocked + filesystem cached)."""

from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest
import respx

from app.services.apple_asn import _state
from app.services.apple_asn.constants import APPLE_ROOT_URLS
from app.services.apple_asn.load_apple_root_certs import load_apple_root_certs
from app.services.apple_asn.reset_caches import reset_caches


@pytest.fixture(autouse=True)
def reset_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    # Send the disk cache under tmp so each test sees a fresh filesystem.
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: tmp_path))  # type: ignore[arg-type]
    reset_caches()
    yield
    reset_caches()


@respx.mock
async def test_load_apple_root_certs_downloads_each_url() -> None:
    for i, url in enumerate(APPLE_ROOT_URLS):
        respx.get(url).mock(return_value=httpx.Response(200, content=bytes([i])))
    certs = await load_apple_root_certs()
    assert len(certs) == len(APPLE_ROOT_URLS)
    assert certs[0] == b"\x00"


@respx.mock
async def test_load_apple_root_certs_caches_in_memory() -> None:
    for i, url in enumerate(APPLE_ROOT_URLS):
        respx.get(url).mock(return_value=httpx.Response(200, content=bytes([i])))
    first = await load_apple_root_certs()
    # Subsequent call must return the cached bytes — change the upstream and prove we don't re-fetch.
    second = await load_apple_root_certs()
    assert first is second
    assert _state.ROOT_CERTS_CACHE is not None


@respx.mock
async def test_load_apple_root_certs_uses_disk_cache_on_next_call(tmp_path: Path) -> None:
    # Pre-populate the disk cache for one of the URLs, then prove load_apple_root_certs reads it from disk without re-fetching.
    cache_dir = tmp_path / ".cache" / "palkietalkie" / "apple_roots"
    cache_dir.mkdir(parents=True, exist_ok=True)
    first_url = APPLE_ROOT_URLS[0]
    cached_name = first_url.rsplit("/", 1)[-1]
    (cache_dir / cached_name).write_bytes(b"DISK")
    # Route still must be defined for the OTHER URLs.
    for url in APPLE_ROOT_URLS[1:]:
        respx.get(url).mock(return_value=httpx.Response(200, content=b"NET"))
    certs = await load_apple_root_certs()
    assert certs[0] == b"DISK"
