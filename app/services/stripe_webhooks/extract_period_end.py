from datetime import UTC, datetime
from typing import Any


def extract_period_end(data: dict[str, Any], *fallback_keys: str) -> datetime | None:
    for key in ("current_period_end", *fallback_keys):
        value = data.get(key)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(int(value), tz=UTC)
    return None
