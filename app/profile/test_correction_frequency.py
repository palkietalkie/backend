from app.profile.correction_frequency import (
    ALL_CORRECTION_FREQUENCIES,
    CORRECTION_FREQUENCY_PERCENT,
    CORRECTION_FREQUENCY_PROMPT,
    DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY,
    coerce_correction_frequency,
)
from app.profile.proficiency import ALL_PROFICIENCIES


def test_default_by_proficiency_covers_every_level_and_is_a_valid_slug() -> None:
    # Onboarding pre-selects from this map, so it must have an entry for every proficiency, each a real correction level.
    assert set(DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY) == ALL_PROFICIENCIES
    for level in DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY.values():
        assert level in ALL_CORRECTION_FREQUENCIES


def test_default_by_proficiency_ramps_up_and_intermediate_is_the_neutral_middle() -> None:
    # A real beginner gets light correction; advanced gets everything; intermediate sits at the 50% middle.
    assert DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY["beginner"] == "rarely"
    assert DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY["intermediate"] == "sometimes"
    assert DEFAULT_CORRECTION_FREQUENCY_BY_PROFICIENCY["advanced"] == "always"


def test_levels_are_the_five_advertised_slugs() -> None:
    assert (
        frozenset({"never", "rarely", "sometimes", "often", "always"}) == ALL_CORRECTION_FREQUENCIES
    )


def test_percent_map_covers_every_level_0_to_100() -> None:
    assert CORRECTION_FREQUENCY_PERCENT == {
        "never": 0,
        "rarely": 25,
        "sometimes": 50,
        "often": 75,
        "always": 100,
    }


def test_prompt_guidance_exists_for_every_level_except_never() -> None:
    # `never` is empty on purpose: assemble_prompt swaps the whole teaching section for an off-note there rather than inserting a sentence.
    assert CORRECTION_FREQUENCY_PROMPT["never"] == ""
    for level in ("rarely", "sometimes", "often", "always"):
        assert CORRECTION_FREQUENCY_PROMPT[level]


def test_coerce_keeps_a_valid_level() -> None:
    assert coerce_correction_frequency("always") == "always"
    assert coerce_correction_frequency("never") == "never"


def test_coerce_defaults_a_stale_or_missing_value_to_the_neutral_middle() -> None:
    assert coerce_correction_frequency(None) == "sometimes"
    assert coerce_correction_frequency("") == "sometimes"
    assert coerce_correction_frequency("banana") == "sometimes"
