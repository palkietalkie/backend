from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class NewsStory:
    title: str
    description: str
    url: str
    source: str


@dataclass(frozen=True)
class Quiz:
    question: str
    answer: str


def _empty_news() -> list[NewsStory]:
    return []


def _empty_quizzes() -> list[Quiz]:
    return []


@dataclass
class DailyContent:
    day: date
    news: list[NewsStory] = field(default_factory=_empty_news)
    quizzes: list[Quiz] = field(default_factory=_empty_quizzes)
