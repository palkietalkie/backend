import uuid
from datetime import UTC, datetime, timedelta

from app.routers.entitlement.check_is_in_trial import check_is_in_trial
from app.routers.entitlement.constants import FREE_TRIAL_DURATION
from app.services.neon.rows import UserRow


def _user(created_at: datetime) -> UserRow:
    now = datetime.now(UTC)
    return UserRow(
        id=uuid.uuid4(),
        clerk_user_id="u",
        email=None,
        premium=False,
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


def test_brand_new_user_is_in_trial() -> None:
    assert check_is_in_trial(_user(datetime.now(UTC))) is True


def test_user_just_inside_window_is_in_trial() -> None:
    assert (
        check_is_in_trial(_user(datetime.now(UTC) - FREE_TRIAL_DURATION + timedelta(hours=1)))
        is True
    )


def test_user_past_window_is_not_in_trial() -> None:
    assert (
        check_is_in_trial(_user(datetime.now(UTC) - FREE_TRIAL_DURATION - timedelta(days=1)))
        is False
    )


def test_naive_created_at_is_treated_as_utc() -> None:
    # A DB driver that strips tzinfo must not crash the comparison, and a just-created naive stamp is still in trial.
    assert check_is_in_trial(_user(datetime.now(UTC).replace(tzinfo=None))) is True
