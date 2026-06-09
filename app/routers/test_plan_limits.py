from httpx import AsyncClient

from app.routers.entitlement.constants import FREE_MINUTES_PER_DAY, FREE_MINUTES_PER_WEEK
from app.services.neon.rows import UserRow


async def test_plan_limits_returns_constants(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    """The endpoint is public/unauthenticated, but reusing the existing app fixture is simpler than building a fresh one."""
    client, _ = app_with_overrides
    resp = await client.get("/plan_limits")
    assert resp.status_code == 200
    body = resp.json()
    assert body["free_minutes_per_day"] == FREE_MINUTES_PER_DAY
    assert body["free_minutes_per_week"] == FREE_MINUTES_PER_WEEK
