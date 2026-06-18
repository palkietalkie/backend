"""Behavioral tests for GET /stats/phrases (list_phrases)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def _seed_phrase(
    db: DBConn,
    user_id: uuid.UUID,
    *,
    phrase: str,
    count: int,
    last_used_at: datetime,
) -> None:
    await db.execute(
        """INSERT INTO phrase_freq (user_id, phrase, count, last_used_at)
           VALUES ($1, $2, $3, $4)""",
        user_id,
        phrase,
        count,
        last_used_at,
    )


async def test_empty_returns_empty_list(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/phrases")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_orders_by_count_desc_then_recency(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    await _seed_phrase(db, user["id"], phrase="kind of", count=3, last_used_at=now)
    await _seed_phrase(
        db, user["id"], phrase="older7", count=7, last_used_at=now - timedelta(hours=3)
    )
    await _seed_phrase(db, user["id"], phrase="newer7", count=7, last_used_at=now)
    await _seed_phrase(db, user["id"], phrase="you know", count=10, last_used_at=now)
    resp = await client.get("/stats/phrases")
    body = resp.json()
    assert [p["count"] for p in body] == [10, 7, 7, 3]
    assert body[1]["phrase"] == "newer7"
    assert body[2]["phrase"] == "older7"


async def test_returns_full_shape(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    await _seed_phrase(db, user["id"], phrase="at the end of the day", count=4, last_used_at=now)
    item = (await client.get("/stats/phrases")).json()[0]
    # Shape matches the iOS PhraseUsage decodable (id, phrase, count, alternatives).
    assert item["id"] == "at the end of the day"
    assert item["phrase"] == "at the end of the day"
    assert item["count"] == 4
    assert item["alternatives"] == []


async def test_limit_and_offset_paginate(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    for i, count in enumerate((5, 4, 3, 2, 1)):
        await _seed_phrase(db, user["id"], phrase=f"p{i}", count=count, last_used_at=now)
    page1 = await client.get("/stats/phrases", params={"limit": 2, "offset": 0})
    page2 = await client.get("/stats/phrases", params={"limit": 2, "offset": 2})
    assert [p["count"] for p in page1.json()] == [5, 4]
    assert [p["count"] for p in page2.json()] == [3, 2]


async def test_only_returns_own_phrases(
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
    await _seed_phrase(
        db, other_id, phrase="leaked phrase", count=99, last_used_at=datetime.now(UTC)
    )
    resp = await client.get("/stats/phrases")
    assert resp.json() == []


async def test_rejects_out_of_range_limit(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/phrases", params={"limit": 999})
    assert resp.status_code == 422
