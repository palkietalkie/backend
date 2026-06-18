"""Behavioral tests for GET /stats/mistakes (list_mistakes)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_mistake(
    db: DBConn,
    user_id: uuid.UUID,
    *,
    original: str,
    corrected: str,
    category: str,
    count: int,
    last_seen_at: datetime,
) -> None:
    await db.execute(
        """INSERT INTO mistakes (id, user_id, original, corrected, category, count, last_seen_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7)""",
        uuid.uuid4(),
        user_id,
        original,
        corrected,
        category,
        count,
        last_seen_at,
    )


async def test_empty_returns_empty_list(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/mistakes")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_orders_by_count_desc_then_recency(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    # Two share count=5; the more recent one must come first within that tie.
    await _seed_mistake(
        db, user["id"], original="a", corrected="an", category="article", count=2, last_seen_at=now
    )
    await _seed_mistake(
        db,
        user["id"],
        original="older5",
        corrected="x",
        category="grammar",
        count=5,
        last_seen_at=now - timedelta(hours=2),
    )
    await _seed_mistake(
        db,
        user["id"],
        original="newer5",
        corrected="x",
        category="grammar",
        count=5,
        last_seen_at=now,
    )
    await _seed_mistake(
        db, user["id"], original="b", corrected="be", category="verb", count=9, last_seen_at=now
    )
    resp = await client.get("/stats/mistakes")
    body = resp.json()
    assert [m["count"] for m in body] == [9, 5, 5, 2]
    # Recency tiebreak inside the count=5 group.
    assert body[1]["original"] == "newer5"
    assert body[2]["original"] == "older5"


async def test_returns_full_shape(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    await _seed_mistake(
        db,
        user["id"],
        original="I has",
        corrected="I have",
        category="subject_verb_agreement",
        count=3,
        last_seen_at=now,
    )
    resp = await client.get("/stats/mistakes")
    item = resp.json()[0]
    # Shape matches the iOS Mistake decodable (id, original, correction, count).
    assert item["id"]
    assert item["original"] == "I has"
    assert item["correction"] == "I have"
    assert item["count"] == 3


async def test_limit_and_offset_paginate(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    # Distinct counts so ordering is deterministic: 5,4,3,2,1.
    for i, count in enumerate((5, 4, 3, 2, 1)):
        await _seed_mistake(
            db,
            user["id"],
            original=f"o{i}",
            corrected=f"c{i}",
            category="grammar",
            count=count,
            last_seen_at=now,
        )
    page1 = await client.get("/stats/mistakes", params={"limit": 2, "offset": 0})
    page2 = await client.get("/stats/mistakes", params={"limit": 2, "offset": 2})
    assert [m["count"] for m in page1.json()] == [5, 4]
    assert [m["count"] for m in page2.json()] == [3, 2]


async def test_only_returns_own_mistakes(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    other_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO users (id, clerk_user_id, email, preferred_name, native_languages,
                              created_at, updated_at)
           VALUES ($1, $2, 'other@palkietalkie.test', 'Other', ARRAY['Japanese'], NOW(), NOW())""",
        other_id,
        f"user_{uuid.uuid4().hex[:12]}",
    )
    now = datetime.now(UTC)
    await _seed_mistake(
        db,
        other_id,
        original="leak",
        corrected="nope",
        category="grammar",
        count=99,
        last_seen_at=now,
    )
    resp = await client.get("/stats/mistakes")
    assert resp.json() == []


async def test_rejects_out_of_range_limit(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/mistakes", params={"limit": 0})
    assert resp.status_code == 422
