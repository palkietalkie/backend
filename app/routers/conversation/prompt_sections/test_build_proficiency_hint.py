from app.routers.conversation.prompt_sections.build_proficiency_hint import build_proficiency_hint


def test_each_level_carries_its_own_cefr_range() -> None:
    ranges = {
        "beginner": "CEFR pre-A1 to A1",
        "lower_intermediate": "CEFR A2",
        "intermediate": "CEFR B1",
        "upper_intermediate": "CEFR B2",
        "advanced": "CEFR C1 to C2",
    }
    for level, cefr in ranges.items():
        assert cefr in build_proficiency_hint(level, "English", "Japanese")


def test_levels_are_differentiated_not_copies() -> None:
    levels = ["beginner", "lower_intermediate", "intermediate", "upper_intermediate", "advanced"]
    hints = [build_proficiency_hint(level, "English", "Japanese") for level in levels]
    assert len(set(hints)) == len(levels)


def test_beginner_scaffolds_in_the_native_language_and_expects_no_sentences() -> None:
    hint = build_proficiency_hint("beginner", "English", "Japanese")
    assert "Speak mostly in Japanese" in hint
    assert "Do NOT expect sentences" in hint


def test_advanced_speaks_native_level_no_accommodation() -> None:
    hint = build_proficiency_hint("advanced", "English", "Japanese")
    assert "no accommodation" in hint


def test_unknown_level_falls_back_to_intermediate() -> None:
    assert build_proficiency_hint("not-a-level", "English", "Japanese") == build_proficiency_hint(
        "intermediate", "English", "Japanese"
    )
