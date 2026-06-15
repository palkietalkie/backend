from datetime import date

from app.daily_content.models import TalkItem
from app.services.neon.db_conn import DBConn


async def save_topic_items(day: date, topic: str, items: list[TalkItem], db: DBConn) -> None:
    # Plain list of dicts: asyncpg's jsonb codec (register_json_codecs.py) calls json.dumps on the value, so pre-serializing would double-encode and store as a JSON-string scalar instead of a JSONB array.
    await db.execute(
        """INSERT INTO daily_content (day, topic, items)
           VALUES ($1, $2, $3)
           ON CONFLICT (day, topic) DO UPDATE
             SET items = EXCLUDED.items,
                 updated_at = now()""",
        day,
        topic,
        [
            {
                "title": item.title,
                "summary": item.summary,
                "source": item.source,
                "image_url": item.image_url,
            }
            for item in items
        ],
    )
