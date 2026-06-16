from httpx import AsyncClient

from app.services.neon.rows import UserRow


async def test_blocked_url_returns_empty_content(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    # SSRF-blocked host: fetch_url_text returns "" with no network call, and the route never errors so a live tool call can't stall.
    resp = await client.get("/recall/web_fetch?url=http://localhost/admin")
    assert resp.status_code == 200
    assert resp.json() == {"content": ""}


async def test_missing_url_is_rejected(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    assert (await client.get("/recall/web_fetch")).status_code == 422
