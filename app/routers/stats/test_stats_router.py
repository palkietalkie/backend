"""Integration tests for /stats endpoints."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_fetch_overview_empty_returns_zeros(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sessions_count"] == 0
    assert body["unique_words"] == 0
    assert body["unique_phrases"] == 0
    assert body["session_total_seconds"] == 0
    assert body["user_talk_pct"] is None
    assert body["speaking_rate_wpm"] is None
    assert body["pitch_min_hz"] is None
    assert body["pitch_max_hz"] is None
    assert isinstance(body["cefr_coverage"], list)
    assert body["day_streak"] == 0


async def test_fetch_overview_counts_sessions_and_streak(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    today = datetime.now(UTC)
    # Two consecutive days of activity ending today.
    for delta in (0, 1):
        sid = uuid.uuid4()
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
               VALUES ($1, $2, $3, 120)""",
            sid,
            user["id"],
            today - timedelta(days=delta),
        )

    resp = await client.get("/stats")
    body = resp.json()
    assert body["sessions_count"] == 2
    assert body["session_total_seconds"] == 240
    assert body["day_streak"] >= 1


async def test_fetch_overview_user_talk_pct_and_wpm(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    sid = uuid.uuid4()
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), 60)""",
        sid,
        user["id"],
    )
    now = datetime.now(UTC)
    # 50 chars of "user" speech (10 words) + 50 chars of "persona" speech => 50% user talk.
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'user', $2, $3, $3)""",
        sid,
        "one two three four five six seven eight nine ten ",
        now,
    )
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'persona', $2, $3, $3)""",
        sid,
        "x" * 50,
        now,
    )

    resp = await client.get("/stats")
    body = resp.json()
    assert body["user_talk_pct"] is not None
    assert body["user_talk_pct"] > 0
    assert body["speaking_rate_wpm"] is not None


async def test_fetch_overview_pitch_range_from_events(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    await db.execute(
        """INSERT INTO events (user_id, event_type, ts, props)
           VALUES ($1, 'pitch_range', NOW(), $2)""",
        user["id"],
        {"min_hz": 80.0, "max_hz": 220.0},
    )
    resp = await client.get("/stats")
    body = resp.json()
    assert body["pitch_min_hz"] == 80.0
    assert body["pitch_max_hz"] == 220.0


async def test_list_mistakes_orders_by_count_desc(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    for original, corrected, count in [("a", "an", 2), ("b", "be", 9), ("c", "see", 5)]:
        await db.execute(
            """INSERT INTO mistakes (id, user_id, original, corrected, category, count, last_seen_at)
               VALUES ($1, $2, $3, $4, 'grammar', $5, NOW())""",
            uuid.uuid4(),
            user["id"],
            original,
            corrected,
            count,
        )
    resp = await client.get("/stats/mistakes")
    body = resp.json()
    counts = [item["count"] for item in body]
    assert counts == sorted(counts, reverse=True)


async def test_list_phrases_orders_by_count_desc(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    for phrase, count in [("p1", 3), ("p2", 10), ("p3", 7)]:
        await db.execute(
            """INSERT INTO phrase_freq (user_id, phrase, count, last_used_at)
               VALUES ($1, $2, $3, NOW())""",
            user["id"],
            phrase,
            count,
        )
    resp = await client.get("/stats/phrases")
    counts = [item["count"] for item in resp.json()]
    assert counts == sorted(counts, reverse=True)


async def test_list_cefr_missing_filters_used_words(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _user = app_with_overrides
    resp = await client.get("/stats/cefr", params={"limit": 5})
    assert resp.status_code == 200
    body: list[dict[str, object]] = resp.json()
    assert isinstance(body, list)
    if body:
        first = body[0]
        assert "lemma" in first
        assert "level" in first


async def test_list_cefr_missing_with_level_filter(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats/cefr", params={"level": "A1", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    for item in body:
        assert item["level"] == "A1"
