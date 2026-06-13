from typing import Any


def diff_attributes(current: dict[str, Any], desired: dict[str, str]) -> dict[str, str]:
    """Return only the desired attributes whose live value differs — the idempotency core. An empty result means nothing changed, so the caller can skip the PATCH."""
    return {k: v for k, v in desired.items() if current.get(k) != v}
