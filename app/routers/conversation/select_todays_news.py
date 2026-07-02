import random

from app.daily_content.constants import POOL_TOPICS
from app.daily_content.models import TalkItem


def select_todays_news(by_topic: dict[str, list[TalkItem]], limit: int) -> list[TalkItem]:
    # Flatten today's news across categories, dropping the timeless pool topics (quizzes) — those aren't news. Random sample so each Talk session surfaces a different cut instead of the same top headlines every time.
    news = [item for topic, items in by_topic.items() if topic not in POOL_TOPICS for item in items]
    if len(news) <= limit:
        return news
    return random.sample(news, limit)  # noqa: S311
