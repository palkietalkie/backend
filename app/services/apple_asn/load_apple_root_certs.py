from pathlib import Path

import httpx

from app.services.apple_asn import _state
from app.services.apple_asn.constants import APPLE_ROOT_URLS


async def load_apple_root_certs() -> list[bytes]:
    if _state.ROOT_CERTS_CACHE is not None:
        return _state.ROOT_CERTS_CACHE
    cache_dir = Path.home() / ".cache" / "palkietalkie" / "apple_roots"
    cache_dir.mkdir(parents=True, exist_ok=True)
    out: list[bytes] = []
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for url in APPLE_ROOT_URLS:
            local = cache_dir / url.rsplit("/", 1)[-1]
            if local.exists():
                out.append(local.read_bytes())
                continue
            resp = await client.get(url)
            resp.raise_for_status()
            local.write_bytes(resp.content)
            out.append(resp.content)
    _state.ROOT_CERTS_CACHE = out
    return out
