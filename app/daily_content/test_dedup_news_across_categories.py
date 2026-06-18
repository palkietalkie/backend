from app.daily_content.dedup_news_across_categories import dedup_news_across_categories
from app.daily_content.models import TalkItem


def _item(title: str, url: str = "") -> TalkItem:
    return TalkItem(title=title, summary="", url=url)


def test_drops_cross_category_duplicate_by_url() -> None:
    first = _item("Market story", "http://x/1")
    dup = _item("Market story", "http://x/1")
    other = _item("Sports story", "http://x/2")
    politics, business = dedup_news_across_categories([[first], [dup, other]])
    assert [i.title for i in politics] == ["Market story"]
    assert [i.title for i in business] == ["Sports story"]


def test_falls_back_to_title_when_url_missing() -> None:
    first = _item("Same headline")
    dup = _item("Same headline")
    a, b = dedup_news_across_categories([[first], [dup]])
    assert len(a) == 1
    assert b == []
