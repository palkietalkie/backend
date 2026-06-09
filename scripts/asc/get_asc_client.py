import httpx

from scripts.asc.constants import ASC_BASE
from scripts.asc.mint_jwt import mint_jwt


def get_asc_client() -> httpx.Client:
    """httpx.Client preconfigured with ASC base URL + a fresh ES256 JWT bearer.

    Caller uses it as a context manager: `with get_asc_client() as client: ...`. The token's lifetime (20 min) is plenty for any single script run; long-running pipelines should mint a fresh client rather than refresh in place.
    """
    return httpx.Client(
        base_url=ASC_BASE,
        headers={"Authorization": f"Bearer {mint_jwt()}"},
        timeout=60.0,
    )
