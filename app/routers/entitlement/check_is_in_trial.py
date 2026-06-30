from datetime import UTC, datetime

from app.routers.entitlement.constants import FREE_TRIAL_DURATION
from app.services.neon.rows import UserRow


def check_is_in_trial(user: UserRow) -> bool:
    """True while a user is inside their first-month free trial (signup + FREE_TRIAL_DURATION). Derived purely from created_at, so it expires on its own with no trial column, cron, or backfill."""
    created = user["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return datetime.now(UTC) < created + FREE_TRIAL_DURATION
