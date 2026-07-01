import uuid
from datetime import UTC, datetime

from app.routers.entitlement.compute_trial_ends_at import compute_trial_ends_at
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


def test_ends_one_trial_duration_after_signup() -> None:
    created = datetime(2026, 1, 1, tzinfo=UTC)
    assert compute_trial_ends_at(_user(created)) == created + FREE_TRIAL_DURATION


def test_naive_created_at_is_treated_as_utc() -> None:
    assert (
        compute_trial_ends_at(_user(datetime(2026, 1, 1)))
        == datetime(2026, 1, 1, tzinfo=UTC) + FREE_TRIAL_DURATION
    )
