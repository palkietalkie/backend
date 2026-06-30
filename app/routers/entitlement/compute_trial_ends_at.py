from datetime import UTC, datetime

from app.routers.entitlement.constants import FREE_TRIAL_DURATION
from app.services.neon.rows import UserRow


def compute_trial_ends_at(user: UserRow) -> datetime:
    """When the user's first-month free trial expires: signup (created_at) + FREE_TRIAL_DURATION. created_at can be tz-naive from some drivers, so normalize to UTC before adding. The single place the trial window's end is computed, so check_is_in_trial and the entitlement response can't drift."""
    created = user["created_at"]
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return created + FREE_TRIAL_DURATION
