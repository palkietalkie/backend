"""Tests for PUT /consent — persisting personalization + product-improvement consent on the users row.

The route maps each bool to a timestamp column (non-null = granted) and stamps consent_screen_seen_at once. Assertions check both the response body and the actual users-row state through the shared transaction connection."""

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_both_true_sets_consent_columns_and_marks_set(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.put(
        "/consent",
        json={"personalization": True, "product_improvement": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"personalization": True, "product_improvement": True, "set": True}
    row = await db.fetchrow(
        """SELECT personalization_consent, product_improvement_consent, consent_screen_seen_at
           FROM users WHERE id = $1""",
        user["id"],
    )
    assert row is not None
    # Granted consent => non-null timestamp; seen-at stamped.
    assert row["personalization_consent"] is not None
    assert row["product_improvement_consent"] is not None
    assert row["consent_screen_seen_at"] is not None


async def test_false_clears_to_null_but_keeps_screen_seen(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    resp = await client.put(
        "/consent",
        json={"personalization": False, "product_improvement": True},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["personalization"] is False
    assert body["product_improvement"] is True
    assert body["set"] is True
    row = await db.fetchrow(
        """SELECT personalization_consent, product_improvement_consent, consent_screen_seen_at
           FROM users WHERE id = $1""",
        user["id"],
    )
    assert row is not None
    # Declined consent => null column; the screen still counts as seen.
    assert row["personalization_consent"] is None
    assert row["product_improvement_consent"] is not None
    assert row["consent_screen_seen_at"] is not None


async def test_consent_screen_seen_at_is_not_overwritten_on_second_update(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    # COALESCE keeps the original first-seen timestamp across re-submissions.
    client, user = app_with_overrides
    first = await client.put(
        "/consent",
        json={"personalization": True, "product_improvement": False},
    )
    assert first.status_code == 200
    seen_after_first = await db.fetchval(
        "SELECT consent_screen_seen_at FROM users WHERE id = $1", user["id"]
    )
    assert seen_after_first is not None

    second = await client.put(
        "/consent",
        json={"personalization": False, "product_improvement": True},
    )
    assert second.status_code == 200
    seen_after_second = await db.fetchval(
        "SELECT consent_screen_seen_at FROM users WHERE id = $1", user["id"]
    )
    # First-seen timestamp is preserved, not refreshed.
    assert seen_after_second == seen_after_first


async def test_missing_field_is_422(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.put("/consent", json={"personalization": True})
    assert resp.status_code == 422
