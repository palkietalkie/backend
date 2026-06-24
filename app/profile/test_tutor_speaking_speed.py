"""Lock in the speaking-speed value set. iOS picker + prompt-hint branching key off these slugs."""

from app.profile.tutor_speaking_speed import (
    ALL_TUTOR_SPEAKING_SPEEDS,
    TUTOR_SPEED_PLAYBACK_RATE,
    coerce_speaking_speed,
)


def test_speeds_matches_advertised_five_level_set() -> None:
    assert (
        frozenset({"very_slow", "slow", "normal", "fast", "very_fast"}) == ALL_TUTOR_SPEAKING_SPEEDS
    )


def test_speeds_size_is_five() -> None:
    assert len(ALL_TUTOR_SPEAKING_SPEEDS) == 5


def test_every_level_has_a_concrete_playback_rate() -> None:
    assert set(TUTOR_SPEED_PLAYBACK_RATE) == set(ALL_TUTOR_SPEAKING_SPEEDS)


def test_rates_within_openai_accepted_range() -> None:
    # session.audio.output.speed accepts 0.25-1.5; anything outside 400s every session at that level.
    for rate in TUTOR_SPEED_PLAYBACK_RATE.values():
        assert 0.25 <= rate <= 1.5


def test_normal_is_natural_speed() -> None:
    assert TUTOR_SPEED_PLAYBACK_RATE["normal"] == 1.0


def test_rates_strictly_increase_slow_to_fast() -> None:
    order = ["very_slow", "slow", "normal", "fast", "very_fast"]
    rates = [TUTOR_SPEED_PLAYBACK_RATE[s] for s in order]
    assert rates == sorted(rates)
    assert len(set(rates)) == len(rates)


def test_beginner_levels_are_a_real_slowdown() -> None:
    # The reason this exists (a beginner like Ayumi): very_slow/slow must be meaningfully below natural, not a token nudge.
    assert TUTOR_SPEED_PLAYBACK_RATE["very_slow"] <= 0.75
    assert TUTOR_SPEED_PLAYBACK_RATE["slow"] < 1.0


def test_coerce_passes_known_levels() -> None:
    for s in ALL_TUTOR_SPEAKING_SPEEDS:
        assert coerce_speaking_speed(s) == s


def test_coerce_defaults_null_and_unknown_to_normal() -> None:
    assert coerce_speaking_speed(None) == "normal"
    assert coerce_speaking_speed("") == "normal"
    assert coerce_speaking_speed("turbo") == "normal"
