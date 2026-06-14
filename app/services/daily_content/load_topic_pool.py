import logging
from typing import Any, cast

from app.daily_content.models import TalkItem
from app.services.neon.db_conn import DBConn

logger = logging.getLogger(__name__)


async def load_topic_pool(topic: str, db: DBConn) -> list[TalkItem]:
    """All accumulated items for a pool topic across every historical day, deduped on (title, summary).

    Used by the router to pick a deterministic daily sample (seeded by today's date) for topics like quizzes that aren't tied to today's news but accumulate over time.
    """
    rows = await db.fetch(
        "SELECT items FROM daily_content WHERE topic = $1",
        topic,
    )
    seen: set[tuple[str, str]] = set()
    out: list[TalkItem] = []
    for row in rows:
        raw = row["items"]
        if not isinstance(raw, list):
            continue
        for entry in cast(list[Any], raw):
            if not isinstance(entry, dict):
                continue
            entry_typed = cast(dict[str, Any], entry)
            title = entry_typed.get("title")
            summary = entry_typed.get("summary")
            if not isinstance(title, str) or not isinstance(summary, str):
                continue
            key = (title, summary)
            if key in seen:
                continue
            seen.add(key)
            source = entry_typed.get("source")
            image_url = entry_typed.get("image_url")
            out.append(
                TalkItem(
                    title=title,
                    summary=summary,
                    source=source if isinstance(source, str) else "",
                    image_url=image_url if isinstance(image_url, str) else "",
                )
            )
    return out
