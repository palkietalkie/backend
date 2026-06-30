from datetime import UTC, datetime

from app.daily_content.models import TalkItem
from app.services.daily_content.parse_stored_items import parse_stored_items
from app.services.neon.db_conn import DBConn


async def load_today_topics(db: DBConn) -> dict[str, list[TalkItem]]:
    # Serve the most recent generated day at or before today, not strictly today. News for a UTC day is generated at 06:00 UTC, so between 00:00 and 06:00 UTC "today" has no row yet, and a late-PT-evening user is already in the next UTC day (hit in real use: every news section rendered empty). Falling back to the latest available day shows yesterday's news instead of nothing. A day is generated all-topics-at-once, so max(day) can't return a partial day.
    rows = await db.fetch(
        """SELECT topic, items FROM daily_content
           WHERE day = (SELECT max(day) FROM daily_content WHERE day <= $1)""",
        datetime.now(UTC).date(),
    )
    return {row["topic"]: parse_stored_items(row["items"]) for row in rows}
