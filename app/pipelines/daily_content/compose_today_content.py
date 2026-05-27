from datetime import date

from app.pipelines.daily_content import _cache
from app.pipelines.daily_content.fetch_news import fetch_news
from app.pipelines.daily_content.generate_quizzes import generate_quizzes
from app.pipelines.daily_content.models import DailyContent


async def compose_today_content() -> DailyContent:
    today = date.today()
    cached = _cache.CACHE.get(today)
    if cached is not None:
        return cached
    news = await fetch_news()
    quizzes = await generate_quizzes(news)
    content = DailyContent(day=today, news=news, quizzes=quizzes)
    _cache.CACHE[today] = content
    # Drop stale days.
    for d in list(_cache.CACHE):
        if d != today:
            _cache.CACHE.pop(d, None)
    return content
