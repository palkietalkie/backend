from datetime import UTC, datetime

import pytest

from app.daily_content.models import TalkItem
from app.services.daily_content.load_today_topics import load_today_topics
from app.services.daily_content.save_topic_items import save_topic_items
from app.services.neon.db_conn import DBConn

pytestmark = pytest.mark.asyncio


def _item(title: str, summary: str = "", source: str = "", image_url: str = "") -> TalkItem:
    return TalkItem(title=title, summary=summary, source=source, image_url=image_url)


async def test_save_then_load_roundtrip(db: DBConn) -> None:
    today = datetime.now(UTC).date()
    politics = [_item("Senate vote on bill X", "Passed 60-40.", "AP", "https://example.com/a.jpg")]
    sports = [_item("Djokovic wins in 5 sets", "At Roland Garros.", "Reuters", "")]
    await save_topic_items(today, "politics", politics, db)
    await save_topic_items(today, "sports", sports, db)
    loaded = await load_today_topics(db)
    assert loaded["politics"] == politics
    assert loaded["sports"] == sports


async def test_save_overwrites_same_topic(db: DBConn) -> None:
    today = datetime.now(UTC).date()
    await save_topic_items(today, "business", [_item("Old")], db)
    await save_topic_items(today, "business", [_item("Fresh", "x")], db)
    loaded = await load_today_topics(db)
    assert [i.title for i in loaded["business"]] == ["Fresh"]


async def test_load_returns_empty_dict_when_no_rows(db: DBConn) -> None:
    assert await load_today_topics(db) == {}


async def test_save_stores_jsonb_arrays_not_string_scalars(db: DBConn) -> None:
    # Regression: asyncpg's jsonb codec already calls json.dumps; pre-stringifying the value here double-encodes and stores a JSON-string scalar instead of a JSONB array. iOS would then get unreadable content. This asserts the stored shape directly so the round-trip can't hide a wrong-shape save.
    await save_topic_items(datetime.now(UTC).date(), "politics", [_item("x", "y")], db)
    row = await db.fetchrow(
        """SELECT jsonb_typeof(items) AS t,
                  jsonb_typeof(items -> 0) AS elem_t,
                  items -> 0 ->> 'title' AS first_title
           FROM daily_content WHERE day = $1 AND topic = $2""",
        datetime.now(UTC).date(),
        "politics",
    )
    assert row is not None
    assert row["t"] == "array"
    # Each element must be a real JSONB object reachable by key — double-encoding (the register_json_codecs.py double-dumps footgun) would make items a JSON-string scalar with no addressable inner objects.
    assert row["elem_t"] == "object"
    assert row["first_title"] == "x"


async def test_load_tolerates_rows_missing_source_or_image_url(db: DBConn) -> None:
    # Historical rows saved before source/image_url existed still load — missing fields read as empty strings, not None and not failures.
    await db.execute(
        """INSERT INTO daily_content (day, topic, items) VALUES ($1, $2, $3)""",
        datetime.now(UTC).date(),
        "politics",
        [{"title": "Old shape", "summary": "no source field"}],
    )
    loaded = await load_today_topics(db)
    assert loaded["politics"] == [_item("Old shape", "no source field", "", "")]
