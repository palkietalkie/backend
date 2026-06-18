"""Tests for DELETE /account — soft-delete the current user.

The route stamps users.deleted_at (never hard-deletes, so total-user counts survive). app_with_overrides bypasses the auth dependency, so these assert the write itself; the rejection-of-deleted-accounts gate is covered in app/auth/test_resolve_current_user.py."""

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_delete_account_stamps_deleted_at(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    before = await db.fetchval("SELECT deleted_at FROM users WHERE id = $1", user["id"])
    assert before is None

    resp = await client.delete("/account")
    assert resp.status_code == 204

    after = await db.fetchval("SELECT deleted_at FROM users WHERE id = $1", user["id"])
    assert after is not None
    # Row is retained, not removed — counts must survive a delete.
    exists = await db.fetchval("SELECT COUNT(*) FROM users WHERE id = $1", user["id"])
    assert exists == 1


async def test_delete_account_is_idempotent_on_timestamp(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    first = await client.delete("/account")
    assert first.status_code == 204
    stamped = await db.fetchval("SELECT deleted_at FROM users WHERE id = $1", user["id"])
    assert stamped is not None

    # Re-issuing the delete keeps the original timestamp (the WHERE deleted_at IS NULL guard no-ops).
    second = await client.delete("/account")
    assert second.status_code == 204
    still = await db.fetchval("SELECT deleted_at FROM users WHERE id = $1", user["id"])
    assert still == stamped
