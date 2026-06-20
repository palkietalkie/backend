from app.profile.format_goals_for_prompt import format_goals_for_prompt


def test_preset_slugs_become_readable_phrases() -> None:
    assert format_goals_for_prompt("job_interview, travel") == "job interviews, travel"


def test_free_text_other_passes_through_untouched() -> None:
    assert format_goals_for_prompt("pass my driving test in English") == (
        "pass my driving test in English"
    )


def test_mixes_slugs_and_free_text() -> None:
    assert format_goals_for_prompt("dating_relationships, chatting with my barista") == (
        "dating and relationships, chatting with my barista"
    )


def test_free_text_with_a_comma_is_reconstructed() -> None:
    # Only exact slug tokens translate; a free-text fragment that splits on its own comma rejoins intact.
    assert format_goals_for_prompt("work, life, and everything") == "work, life, and everything"


def test_blank_and_whitespace_yield_empty() -> None:
    assert format_goals_for_prompt("") == ""
    assert format_goals_for_prompt("  ,  ") == ""


def test_every_goal_has_a_prompt_phrase() -> None:
    from app.profile.goal import ALL_GOALS, GOAL_PROMPT_PHRASES

    assert set(GOAL_PROMPT_PHRASES) == ALL_GOALS, "each Goal must map to a readable prompt phrase"
