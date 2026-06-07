"""Tests for load_topic_pool — aggregates and dedupes items across history."""

from datetime import UTC, datetime, timedelta

import pytest

from app.pipelines.daily_content.models import TalkItem
from app.services.daily_content.load_topic_pool import load_topic_pool
from app.services.daily_content.save_topic_items import save_topic_items
from app.services.neon.db_conn import DBConn


def _item(title: str, summary: str = "s") -> TalkItem:
    return TalkItem(title=title, summary=summary, source="", image_url="")


async def test_load_topic_pool_empty_when_no_rows(db: DBConn) -> None:
    assert await load_topic_pool("quizzes", db) == []


async def test_load_topic_pool_dedupes_on_title_summary(db: DBConn) -> None:
    today = datetime.now(UTC).date()
    yesterday = today - timedelta(days=1)
    await save_topic_items(yesterday, "quizzes", [_item("dup", "same"), _item("uniq")], db)
    await save_topic_items(today, "quizzes", [_item("dup", "same"), _item("new")], db)
    pool = await load_topic_pool("quizzes", db)
    titles = [i.title for i in pool]
    assert sorted(titles) == ["dup", "new", "uniq"]


async def test_load_topic_pool_ignores_non_list_rows(db: DBConn) -> None:
    # Synthesize a corrupt row directly (jsonb of an object, not array).
    await db.execute(
        "INSERT INTO daily_content (day, topic, items) VALUES (CURRENT_DATE, $1, $2)",
        "quizzes",
        {"bogus": True},
    )
    assert await load_topic_pool("quizzes", db) == []


async def test_load_topic_pool_ignores_non_dict_entries(db: DBConn) -> None:
    await db.execute(
        "INSERT INTO daily_content (day, topic, items) VALUES (CURRENT_DATE, $1, $2)",
        "quizzes",
        ["just a string", 42],
    )
    assert await load_topic_pool("quizzes", db) == []


async def test_load_topic_pool_skips_items_missing_title_or_summary(db: DBConn) -> None:
    await db.execute(
        "INSERT INTO daily_content (day, topic, items) VALUES (CURRENT_DATE, $1, $2)",
        "quizzes",
        [{"title": "ok", "summary": "ok"}, {"title": "no summary"}, {"summary": "no title"}],
    )
    pool = await load_topic_pool("quizzes", db)
    assert len(pool) == 1
    assert pool[0].title == "ok"


@pytest.mark.parametrize("bad_value", [None, 7, ["nested"]])
async def test_load_topic_pool_treats_non_str_source_image_as_empty(
    db: DBConn, bad_value: object
) -> None:
    await db.execute(
        "INSERT INTO daily_content (day, topic, items) VALUES (CURRENT_DATE, $1, $2)",
        "quizzes",
        [{"title": "t", "summary": "s", "source": bad_value, "image_url": bad_value}],
    )
    pool = await load_topic_pool("quizzes", db)
    assert pool[0].source == ""
    assert pool[0].image_url == ""
