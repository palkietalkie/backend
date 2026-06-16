from app.daily_content.models import TalkItem
from app.services.daily_content.parse_stored_items import parse_stored_items
from app.services.neon.db_conn import DBConn


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
        for item in parse_stored_items(row["items"]):
            key = (item.title, item.summary)
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out
