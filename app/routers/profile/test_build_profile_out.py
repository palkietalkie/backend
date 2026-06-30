import uuid
from datetime import UTC, datetime

from app.routers.profile.build_profile_out import build_profile_out
from app.services.neon.rows import UserRow

_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _user_row(
    target_language: str = "Mandarin Chinese",
    proficiency: str = "beginner",
    tutor_speaking_speed: str = "slow",
    native_languages: list[str] | None = None,
    target_accents: list[str] | None = None,
) -> UserRow:
    return {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "clerk_user_id": "u_1",
        "email": "a@b.com",
        "premium": False,
        "premium_ends_at": None,
        "created_at": _NOW,
        "updated_at": _NOW,
        "preferred_name": "Yas",
        "goals": None,
        "location_city": None,
        "timezone": None,
        "personalization_consent": None,
        "product_improvement_consent": None,
        "consent_screen_seen_at": None,
        "name_pronunciation": None,
        "target_language": target_language,
        "tutor_speaking_speed": tutor_speaking_speed,
        "proficiency": proficiency,
        "native_languages": native_languages if native_languages is not None else ["English"],
        "target_accents": target_accents if target_accents is not None else ["Beijing Standard"],
        "deleted_at": None,
    }


def test_valid_values_pass_through_unchanged() -> None:
    out = build_profile_out(_user_row())
    assert out.target_language == "Mandarin Chinese"
    assert out.proficiency == "beginner"
    assert out.tutor_speaking_speed == "slow"
    assert out.target_accents == ["Beijing Standard"]
    assert out.native_languages == ["English"]


def test_unknown_target_language_coerced_to_english() -> None:
    out = build_profile_out(_user_row(target_language="Klingonese"))
    assert out.target_language == "English"


def test_unknown_proficiency_coerced_to_intermediate() -> None:
    assert build_profile_out(_user_row(proficiency="expert")).proficiency == "intermediate"


def test_unknown_speed_coerced_to_normal() -> None:
    assert (
        build_profile_out(_user_row(tutor_speaking_speed="ludicrous")).tutor_speaking_speed
        == "normal"
    )


def test_unknown_accent_is_filtered_out() -> None:
    out = build_profile_out(_user_row(target_accents=["Beijing Standard", "Renamed Old Accent"]))
    assert out.target_accents == ["Beijing Standard"]


def test_unknown_native_language_is_filtered_out() -> None:
    out = build_profile_out(_user_row(native_languages=["English", "Martian"]))
    assert out.native_languages == ["English"]


def test_all_invalid_does_not_raise_and_returns_defaults() -> None:
    # The core guarantee: GET /profile must never 500 on stale enum values, so a fully-drifted row degrades to valid defaults instead of raising (which would blank the frozen build-28 profile screen).
    out = build_profile_out(
        _user_row(
            target_language="???",
            proficiency="???",
            tutor_speaking_speed="???",
            native_languages=["???"],
            target_accents=["???"],
        )
    )
    assert out.target_language == "English"
    assert out.proficiency == "intermediate"
    assert out.tutor_speaking_speed == "normal"
    assert out.native_languages == []
    assert out.target_accents == []
