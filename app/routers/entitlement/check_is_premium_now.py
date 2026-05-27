from datetime import UTC, datetime

from app.services.neon.rows import UserRow


def check_is_premium_now(user: UserRow) -> bool:
    if not user["premium"]:
        return False
    ends_at = user["premium_ends_at"]
    if ends_at is None:
        return True
    if ends_at.tzinfo is None:
        ends_at = ends_at.replace(tzinfo=UTC)
    return ends_at > datetime.now(UTC)
