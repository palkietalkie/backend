"""Behavioral tests for GET /stats (fetch_overview)."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


async def test_empty_user_returns_zeroed_overview(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["day_streak"] == 0
    assert body["session_total_seconds"] == 0
    assert body["sessions_count"] == 0
    assert body["unique_words"] == 0
    assert body["unique_phrases"] == 0
    assert body["user_talk_pct"] is None
    assert body["speaking_rate_wpm"] is None
    assert body["pitch_min_hz"] is None
    assert body["pitch_max_hz"] is None
    assert body["affinity"] == 0
    # CEFR coverage is always present (computed from the static reference list) even with no data.
    assert isinstance(body["cefr_coverage"], list)
    assert body["cefr_coverage"], "expected one coverage row per CEFR level"
    levels = [row["level"] for row in body["cefr_coverage"]]
    assert levels == ["A1", "A2", "B1", "B2", "C1", "C2"]
    for row in body["cefr_coverage"]:
        assert row["used_words"] == 0
        assert row["coverage_pct"] == 0.0
        assert row["total_words"] >= 0


async def test_sums_duration_and_counts_sessions(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    now = datetime.now(UTC)
    for seconds in (90, 150):
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
               VALUES ($1, $2, $3, $4)""",
            uuid.uuid4(),
            user["id"],
            now,
            seconds,
        )
    resp = await client.get("/stats")
    body = resp.json()
    assert body["sessions_count"] == 2
    assert body["session_total_seconds"] == 240


async def test_day_streak_counts_consecutive_utc_days(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    today = datetime.now(UTC)
    # Today, yesterday, day-before — 3 consecutive days, then a gap, then one more.
    for delta in (0, 1, 2, 5):
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
               VALUES ($1, $2, $3, 60)""",
            uuid.uuid4(),
            user["id"],
            today - timedelta(days=delta),
        )
    resp = await client.get("/stats")
    body = resp.json()
    # Streak stops at the gap: today + yesterday + day-before = 3.
    assert body["day_streak"] == 3


async def test_day_streak_survives_no_session_today(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    today = datetime.now(UTC)
    # No session today, but yesterday + day-before. Streak should not reset to 0 mid-day.
    for delta in (1, 2):
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
               VALUES ($1, $2, $3, 60)""",
            uuid.uuid4(),
            user["id"],
            today - timedelta(days=delta),
        )
    resp = await client.get("/stats")
    assert resp.json()["day_streak"] == 2


async def test_unique_words_and_phrases_count_rows(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    for lemma in ("hello", "world", "run"):
        await db.execute(
            "INSERT INTO word_freq (user_id, lemma, count) VALUES ($1, $2, 1)",
            user["id"],
            lemma,
        )
    for phrase in ("kind of", "you know"):
        await db.execute(
            "INSERT INTO phrase_freq (user_id, phrase, count) VALUES ($1, $2, 1)",
            user["id"],
            phrase,
        )
    resp = await client.get("/stats")
    body = resp.json()
    assert body["unique_words"] == 3
    assert body["unique_phrases"] == 2


async def test_user_talk_pct_and_speaking_rate(
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
    # 50 chars of user text (10 words) + 50 chars of persona text => exactly 50% user talk.
    user_text = "one two three four five six seven eight nine ten "
    assert len(user_text) == 49  # guard the proxy math the route depends on
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'user', $2, $3, $3)""",
        sid,
        user_text,
        now,
    )
    await db.execute(
        """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
           VALUES ($1, 'persona', $2, $3, $3)""",
        sid,
        "y" * 49,
        now,
    )
    resp = await client.get("/stats")
    body = resp.json()
    assert body["user_talk_pct"] == 0.5
    # user_talk_seconds = 60 * 0.5 = 30s = 0.5 min; 10 words / 0.5 = 20 wpm.
    assert body["speaking_rate_wpm"] == 20.0


async def test_pitch_range_from_events(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    for lo, hi in ((90.0, 200.0), (80.0, 220.0)):
        await db.execute(
            """INSERT INTO events (user_id, event_type, ts, props)
               VALUES ($1, 'pitch_range', NOW(), $2)""",
            user["id"],
            {"min_hz": lo, "max_hz": hi},
        )
    resp = await client.get("/stats")
    # The actual endpoints across sessions: lowest 80, highest 220.
    body = resp.json()
    assert body["pitch_min_hz"] == 80.0
    assert body["pitch_max_hz"] == 220.0


async def test_affinity_weights_combines_and_penalizes_reactions(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, user = app_with_overrides
    # Session 1: 2 laughs + 1 cheer + 1 sigh. Session 2: 1 gasp + 1 groan.
    # Weights: laugh=3, cheer=2, gasp=1, sigh=-2, groan=-2 (negatives penalize).
    for props in (
        {"session_id": str(uuid.uuid4()), "laugh": 2, "cheer": 1, "gasp": 0, "sigh": 1, "groan": 0},
        {"session_id": str(uuid.uuid4()), "laugh": 0, "cheer": 0, "gasp": 1, "sigh": 0, "groan": 1},
    ):
        await db.execute(
            """INSERT INTO events (user_id, event_type, ts, props)
               VALUES ($1, 'ai_emotion', NOW(), $2)""",
            user["id"],
            props,
        )
    resp = await client.get("/stats")
    # earned = 3*2 + 2*1 + 1*1 = 9; penalty = 2*1 (sigh) + 2*1 (groan) = 4.
    # Normalized favorability ratio: round(100 * (9 - 4) / (9 + 4)) = round(38.46) = 38.
    assert resp.json()["affinity"] == 38


async def test_overview_is_scoped_to_the_user(
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
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), 999)""",
        uuid.uuid4(),
        other_id,
    )
    resp = await client.get("/stats")
    body = resp.json()
    assert body["sessions_count"] == 0
    assert body["session_total_seconds"] == 0
