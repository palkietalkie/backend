from app.daily_content.models import TalkItem
from app.routers.conversation.prompt_sections.build_todays_news_section import (
    build_todays_news_section,
)


def test_renders_headlines_with_summaries() -> None:
    news = [TalkItem(title="Local team wins the cup", summary="in extra time")]
    out = build_todays_news_section(news)
    assert "## In the news today" in out
    assert "Local team wins the cup" in out
    assert "in extra time" in out
    # Framing must steer AWAY from reciting the list — the news is opener fuel, not the topic.
    assert "don't recite" in out.lower()
