from app.routers.entitlement.check_is_in_trial import check_is_in_trial
from app.routers.entitlement.check_is_premium_now import check_is_premium_now
from app.services.neon.rows import UserRow


def check_has_full_access(user: UserRow) -> bool:
    """Uncapped, premium-equivalent access: a paying premium subscriber OR a user still inside their first-month free trial. The single predicate the free-cap enforcement and the paid-transcription tier gate on, so a trial user gets the same unlimited, full-quality experience a subscriber does."""
    return check_is_premium_now(user) or check_is_in_trial(user)
