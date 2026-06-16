from datetime import UTC, datetime

from app.daily_content.models import TalkItem
from app.services.daily_content.parse_stored_items import parse_stored_items
from app.services.neon.db_conn import DBConn


async def load_today_topics(db: DBConn) -> dict[str, list[TalkItem]]:
    rows = await db.fetch(
        "SELECT topic, items FROM daily_content WHERE day = $1",
        datetime.now(UTC).date(),
    )
    return {row["topic"]: parse_stored_items(row["items"]) for row in rows}
