"""Tests for GET /content/today."""

from datetime import UTC, datetime

from httpx import AsyncClient

from app.pipelines.daily_content.models import TalkItem
from app.services.daily_content.save_topic_items import save_topic_items
from app.services.neon.db_conn import DBConn
from app.services.neon.rows import UserRow


def _item(title: str) -> TalkItem:
    return TalkItem(title=title, summary="x", source="AP", image_url="https://img/x.jpg")


async def test_fetch_today_content_empty_returns_all_topics(
    app_with_overrides: tuple[AsyncClient, UserRow],
) -> None:
    client, _ = app_with_overrides
    resp = await client.get("/content/today")
    assert resp.status_code == 200
    body = resp.json()
    topics = [s["topic"] for s in body["sections"]]
    # All four topics declared in TOPICS appear, even when empty.
    assert topics == ["politics", "business", "sports", "quizzes"]
    for section in body["sections"]:
        assert section["items"] == []


async def test_fetch_today_content_returns_news_items(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    today = datetime.now(UTC).date()
    await save_topic_items(today, "politics", [_item("Bill X passes")], db)
    resp = await client.get("/content/today")
    politics_section = next(s for s in resp.json()["sections"] if s["topic"] == "politics")
    assert politics_section["items"][0]["title"] == "Bill X passes"
    assert politics_section["items"][0]["source"] == "AP"


async def test_fetch_today_content_pool_samples_quizzes(
    app_with_overrides: tuple[AsyncClient, UserRow], db: DBConn
) -> None:
    client, _ = app_with_overrides
    today = datetime.now(UTC).date()
    quizzes = [_item(f"q{i}") for i in range(20)]
    await save_topic_items(today, "quizzes", quizzes, db)
    resp = await client.get("/content/today")
    quizzes_section = next(s for s in resp.json()["sections"] if s["topic"] == "quizzes")
    # POOL_SAMPLE_SIZE = 10, deterministically sampled.
    assert len(quizzes_section["items"]) == 10
