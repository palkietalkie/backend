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


@dataclass
class DailyContent:
    day: date
    news: list[NewsStory] = field(default_factory=list)
    quizzes: list[Quiz] = field(default_factory=list)
