from dataclasses import dataclass


@dataclass(frozen=True)
class TalkItem:
    # Flat shape across all topics. News items populate source + image_url for attribution and visual; quiz items leave both empty.
    title: str
    summary: str
    source: str = ""
    image_url: str = ""
    # Source article URL, kept for attribution and a future "read full story" link. Empty for quizzes.
    url: str = ""
    # Full article body, fetched server-side at generation time so the model always has real depth instead of NewsAPI's one-line blurb in summary. Empty for quizzes and when the fetch fails (the prompt then falls back to summary).
    details: str = ""
