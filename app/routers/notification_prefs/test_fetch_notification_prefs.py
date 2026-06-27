from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_fetch_returns_defaults_when_no_row(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    # A user who never touched settings reads the same enabled/hour the scheduler assumes for a missing row.
    client, _ = app_with_overrides
    resp = await client.get("/notification-prefs")
    assert resp.status_code == 200
    assert resp.json() == {"reminders_enabled": True, "reminder_hour_local": 19}


async def test_fetch_returns_stored_values(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await db.execute(
        "INSERT INTO notification_prefs (user_id, reminders_enabled, reminder_hour_local) VALUES ($1, FALSE, 8)",
        user["id"],
    )
    resp = await client.get("/notification-prefs")
    assert resp.json() == {"reminders_enabled": False, "reminder_hour_local": 8}
