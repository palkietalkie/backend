"""Lock in the speaking-speed value set. iOS picker + prompt-hint branching key off these slugs."""

from app.profile.tutor_speaking_speed import ALL_TUTOR_SPEAKING_SPEEDS


def test_speeds_matches_advertised_five_level_set() -> None:
    assert (
        frozenset({"very_slow", "slow", "normal", "fast", "very_fast"}) == ALL_TUTOR_SPEAKING_SPEEDS
    )


def test_speeds_size_is_five() -> None:
    assert len(ALL_TUTOR_SPEAKING_SPEEDS) == 5
