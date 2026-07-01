import uuid
from datetime import UTC, datetime, timedelta

from app.routers.entitlement.check_has_full_access import check_has_full_access
from app.routers.entitlement.constants import FREE_TRIAL_DURATION
from app.services.neon.rows import UserRow

_PAST_TRIAL = datetime.now(UTC) - FREE_TRIAL_DURATION - timedelta(days=1)


def _user(*, premium: bool, created_at: datetime) -> UserRow:
    now = datetime.now(UTC)
    return UserRow(
        id=uuid.uuid4(),
        clerk_user_id="u",
        email=None,
        premium=premium,
        premium_ends_at=None,
        created_at=created_at,
        updated_at=now,
        preferred_name=None,
        name_pronunciation=None,
        native_languages=["English"],
        target_accents=[],
        target_language="English",
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        correction_frequency="sometimes",
        goals=None,
        location_city=None,
        timezone=None,
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
        deleted_at=None,
    )


def test_paying_premium_past_trial_has_full_access() -> None:
    assert check_has_full_access(_user(premium=True, created_at=_PAST_TRIAL)) is True


def test_trial_user_without_premium_has_full_access() -> None:
    assert check_has_full_access(_user(premium=False, created_at=datetime.now(UTC))) is True


def test_post_trial_free_user_has_no_full_access() -> None:
    assert check_has_full_access(_user(premium=False, created_at=_PAST_TRIAL)) is False
