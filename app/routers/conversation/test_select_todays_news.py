from app.daily_content.models import TalkItem
from app.routers.conversation.select_todays_news import select_todays_news


def _item(title: str) -> TalkItem:
    return TalkItem(title=title, summary="summary")


def test_excludes_pool_topics_and_caps_at_limit() -> None:
    by_topic = {
        "politics": [_item("p1"), _item("p2")],
        "business": [_item("b1")],
        "quizzes": [_item("q1"), _item("q2")],  # pool topic — timeless, NOT news
    }
    out = select_todays_news(by_topic, limit=2)
    assert len(out) == 2
    titles = {i.title for i in out}
    assert not (titles & {"q1", "q2"}), "quizzes (a pool topic) must never be surfaced as news"
    assert titles <= {"p1", "p2", "b1"}


def test_returns_all_news_when_fewer_than_limit() -> None:
    by_topic = {"politics": [_item("p1")], "business": [_item("b1")]}
    assert {i.title for i in select_todays_news(by_topic, limit=5)} == {"p1", "b1"}


def test_empty_when_only_pool_topics() -> None:
    assert select_todays_news({"quizzes": [_item("q1")]}, limit=3) == []
