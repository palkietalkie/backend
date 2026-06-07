import uuid
from datetime import UTC, datetime

from app.services.neon.rows import UserRow


def _user(**overrides: object) -> UserRow:
    base = UserRow(
        id=uuid.uuid4(),
        clerk_user_id="user_test",
        email="ayumi@example.com",
        premium=False,
        premium_ends_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name="Ayumi",
        name_pronunciation=None,
        native_languages=["Japanese"],
        target_language="English",
        target_accents=[],
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=None,
        location_city=None,
        timezone=None,
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
    )
    # Pyright sees UserRow as TypedDict; runtime dict update accepts the overrides.
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


def test_prefers_name_and_email_when_both_present() -> None:
    from app.services.slack.format_user_label import format_user_label

    assert format_user_label(_user()) == "Ayumi <ayumi@example.com>"


def test_falls_back_to_email_when_name_missing() -> None:
    from app.services.slack.format_user_label import format_user_label

    user = _user(display_name=None)
    assert format_user_label(user) == "ayumi@example.com"


def test_falls_back_to_name_when_email_missing() -> None:
    from app.services.slack.format_user_label import format_user_label

    user = _user(email=None)
    assert format_user_label(user) == "Ayumi"


def test_falls_back_to_uuid_when_name_and_email_missing() -> None:
    from app.services.slack.format_user_label import format_user_label

    user = _user(display_name=None, email=None)
    assert format_user_label(user) == str(user["id"])
