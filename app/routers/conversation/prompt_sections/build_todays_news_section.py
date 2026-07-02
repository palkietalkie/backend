from app.daily_content.models import TalkItem


def build_todays_news_section(news: list[TalkItem]) -> str:
    lines = "\n".join(
        f"- {item.title}" + (f" — {item.summary}" if item.summary else "") for item in news
    )
    return f"""## In the news today
Real headlines from today, so you can bring one up naturally when it fits (a timely opener, or if it comes up). Draw on them, don't recite them as a list or force one in.
{lines}"""
