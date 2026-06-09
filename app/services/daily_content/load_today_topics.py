import logging
from datetime import UTC, datetime
from typing import Any, cast

from app.pipelines.daily_content.models import TalkItem
from app.services.neon.db_conn import DBConn

logger = logging.getLogger(__name__)


def _as_items(raw: Any, topic: str) -> list[TalkItem]:
    if not isinstance(raw, list):
        logger.error("daily_content[%s]: expected list, got %s", topic, type(raw).__name__)
        return []
    items_raw = cast(list[Any], raw)
    out: list[TalkItem] = []
    for entry in items_raw:
        if not isinstance(entry, dict):
            logger.error("daily_content[%s]: non-dict item in jsonb array", topic)
            continue
        entry_typed = cast(dict[str, Any], entry)
        title = entry_typed.get("title")
        summary = entry_typed.get("summary")
        if not isinstance(title, str) or not isinstance(summary, str):
            continue
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


async def load_today_topics(db: DBConn) -> dict[str, list[TalkItem]]:
    rows = await db.fetch(
        "SELECT topic, items FROM daily_content WHERE day = $1",
        datetime.now(UTC).date(),
    )
    return {row["topic"]: _as_items(row["items"], row["topic"]) for row in rows}
