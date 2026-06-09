from dataclasses import dataclass


@dataclass(frozen=True)
class TalkItem:
    # Flat shape across all topics. News items populate source + image_url for attribution and visual; quiz items leave both empty.
    title: str
    summary: str
    source: str
    image_url: str
