from datetime import UTC, datetime

from app.routers.entitlement.compute_trial_ends_at import compute_trial_ends_at
from app.services.neon.rows import UserRow


def check_is_in_trial(user: UserRow) -> bool:
    """True while a user is inside their first-month free trial (signup + FREE_TRIAL_DURATION). Derived purely from created_at, so it expires on its own with no trial column, cron, or backfill."""
    return datetime.now(UTC) < compute_trial_ends_at(user)
