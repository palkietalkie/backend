import logging
from typing import Any

from pydantic import TypeAdapter, ValidationError

from app.daily_content.models import TalkItem

logger = logging.getLogger(__name__)

# Pydantic validates a single jsonb object into a typed TalkItem (it handles stdlib dataclasses), so callers never hand-walk untyped jsonb or cast. Missing source/image_url/url/details fall back to "" for rows written before those fields existed.
_ITEM_ADAPTER = TypeAdapter(TalkItem)


def _validate_one(entry: object) -> TalkItem | None:
    try:
        return _ITEM_ADAPTER.validate_python(entry)
    except ValidationError:
        return None


def parse_stored_items(raw: Any) -> list[TalkItem]:
    """Validate a daily_content.items jsonb array into typed TalkItems, skipping any malformed entry.

    Per-item on purpose: one bad entry must not drop the rest of the day's content. A non-iterable value (corrupt row) yields []. The jsonb value is genuinely Any (asyncpg), iterated directly so its elements stay Any rather than narrowing to Unknown.
    """
    try:
        entries = list(raw)
    except TypeError:
        return []
    items = [item for entry in entries if (item := _validate_one(entry)) is not None]
    if len(items) != len(entries):
        logger.warning(
            "daily_content: %d of %d stored items were malformed and skipped",
            len(entries) - len(items),
            len(entries),
        )
    return items
