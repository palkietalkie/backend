"""Tests for the small neon helper functions that aren't covered yet.

Covers normalize_neon_url + the upsert/fetch helpers via the real test container.
"""

import uuid
from datetime import UTC, datetime, timedelta

from app.services.neon.db_conn import DBConn
from app.services.neon.fetch_persona_by_id import fetch_persona_by_id
from app.services.neon.fetch_session_user_turns import fetch_session_user_turns
from app.services.neon.list_user_lemmas import list_user_lemmas
from app.services.neon.normalize_neon_url import normalize_neon_url
from app.services.neon.rows import UserRow
from app.services.neon.sum_seconds_used_today import sum_seconds_used_today
from app.services.neon.upsert_mistakes import upsert_mistakes
from app.services.neon.upsert_phrase_freq import upsert_phrase_freq
from app.services.neon.upsert_word_freq import upsert_word_freq


def test_normalize_neon_url_strips_asyncpg_prefix() -> None:
    assert normalize_neon_url("postgresql+asyncpg://u:p@h/db") == "postgresql://u:p@h/db"


def test_normalize_neon_url_drops_sslmode_and_channel_binding() -> None:
    out = normalize_neon_url("postgresql://u:p@h/db?sslmode=require&channel_binding=disable&app=x")
    assert "sslmode" not in out
    assert "channel_binding" not in out
    assert "app=x" in out


def test_normalize_neon_url_keeps_url_unchanged_when_no_query() -> None:
    assert normalize_neon_url("postgresql://u:p@h/db") == "postgresql://u:p@h/db"


async def _seed_user_and_session(db: DBConn) -> tuple[uuid.UUID, uuid.UUID]:
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium, timezone) VALUES ($1, $2, FALSE, 'UTC')",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    session_id = uuid.uuid4()
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, NOW(), 60)""",
        session_id,
        user_id,
    )
    return user_id, session_id


async def test_fetch_session_user_turns_returns_user_only(db: DBConn) -> None:
    _user_id, session_id = await _seed_user_and_session(db)
    now = datetime.now(UTC)
    rows = [("user", "hello"), ("persona", "hi"), ("user", "world")]
    for idx, (speaker, text) in enumerate(rows):
        ts = now + timedelta(seconds=idx)
        await db.execute(
            """INSERT INTO transcripts (session_id, speaker, text, started_at, ended_at)
               VALUES ($1, $2, $3, $4, $4)""",
            session_id,
            speaker,
            text,
            ts,
        )
    out = await fetch_session_user_turns(session_id, db)
    assert sorted(out) == ["hello", "world"]


async def test_fetch_persona_by_id_returns_none_for_unknown(db: DBConn) -> None:
    out = await fetch_persona_by_id(db, uuid.uuid4())
    assert out is None


async def test_upsert_word_freq_inserts_then_increments(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    n = await upsert_word_freq(user_id, {"hello": 2, "world": 1}, db)
    assert n == 2
    # Same user, same lemma: count must increment.
    await upsert_word_freq(user_id, {"hello": 3}, db)
    row = await db.fetchrow(
        "SELECT count FROM word_freq WHERE user_id = $1 AND lemma = 'hello'", user_id
    )
    assert row is not None
    assert row["count"] == 5


async def test_upsert_word_freq_empty_dict_returns_zero(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    assert await upsert_word_freq(user_id, {}, db) == 0


async def test_list_user_lemmas_returns_set(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    await upsert_word_freq(user_id, {"a": 1, "b": 1}, db)
    out = await list_user_lemmas(db, user_id)
    assert out == {"a", "b"}


async def test_upsert_phrase_freq_inserts_then_increments(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    n = await upsert_phrase_freq(user_id, [("at the end of the day", 1)], db)
    assert n == 1
    await upsert_phrase_freq(user_id, [("at the end of the day", 2)], db)
    row = await db.fetchrow(
        "SELECT count FROM phrase_freq WHERE user_id = $1 AND phrase = $2",
        user_id,
        "at the end of the day",
    )
    assert row is not None
    assert row["count"] == 3


async def test_upsert_phrase_freq_empty_returns_zero(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    assert await upsert_phrase_freq(user_id, [], db) == 0


async def test_upsert_mistakes_inserts_then_increments(db: DBConn) -> None:
    from app.post_session_nlp.mistake_detection.mistake_record import MistakeRecord

    user_id, _ = await _seed_user_and_session(db)
    n = await upsert_mistakes(user_id, [MistakeRecord("I goed", "I went", "grammar")], db)
    assert n == 1
    await upsert_mistakes(user_id, [MistakeRecord("I goed", "I went", "grammar")], db)
    row = await db.fetchrow(
        "SELECT count FROM mistakes WHERE user_id = $1 AND original = $2",
        user_id,
        "I goed",
    )
    assert row is not None
    assert row["count"] == 2


async def test_upsert_mistakes_empty_returns_zero(db: DBConn) -> None:
    user_id, _ = await _seed_user_and_session(db)
    assert await upsert_mistakes(user_id, [], db) == 0


async def test_sum_seconds_used_today_counts_recent_sessions(db: DBConn) -> None:
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium, timezone) VALUES ($1, $2, FALSE, 'UTC')",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    for dur in (30, 90, 60):
        await db.execute(
            """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
               VALUES ($1, $2, NOW(), $3)""",
            uuid.uuid4(),
            user_id,
            dur,
        )
    now = datetime.now(UTC)
    user_row = UserRow(
        id=user_id,
        clerk_user_id="x",
        email=None,
        premium=False,
        premium_ends_at=None,
        created_at=now,
        updated_at=now,
        preferred_name=None,
        name_pronunciation=None,
        native_languages=["English"],
        target_accents=[],
        target_language="English",
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=None,
        location_city=None,
        timezone="UTC",
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
        deleted_at=None,
    )
    assert await sum_seconds_used_today(user_row, db) == 180


async def test_sum_seconds_used_today_excludes_yesterday(db: DBConn) -> None:
    user_id = uuid.uuid4()
    await db.execute(
        "INSERT INTO users (id, clerk_user_id, premium, timezone) VALUES ($1, $2, FALSE, 'UTC')",
        user_id,
        f"u_{user_id.hex[:8]}",
    )
    await db.execute(
        """INSERT INTO conversation_sessions (id, user_id, started_at, duration_seconds)
           VALUES ($1, $2, $3, 60)""",
        uuid.uuid4(),
        user_id,
        datetime.now(UTC) - timedelta(days=2),
    )
    now = datetime.now(UTC)
    user_row = UserRow(
        id=user_id,
        clerk_user_id="x",
        email=None,
        premium=False,
        premium_ends_at=None,
        created_at=now,
        updated_at=now,
        preferred_name=None,
        name_pronunciation=None,
        native_languages=["English"],
        target_accents=[],
        target_language="English",
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=None,
        location_city=None,
        timezone="UTC",
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
        deleted_at=None,
    )
    assert await sum_seconds_used_today(user_row, db) == 0
