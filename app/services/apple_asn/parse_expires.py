from datetime import UTC, datetime
from typing import Any


def parse_expires(txn: dict[str, Any], renewal: dict[str, Any]) -> datetime | None:
    ms = txn.get("expiresDate") or renewal.get("renewalDate")
    if isinstance(ms, (int, float)):
        return datetime.fromtimestamp(int(ms) / 1000, tz=UTC)
    return None
