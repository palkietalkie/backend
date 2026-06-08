"""Lock in the proficiency value set. iOS picker + DB enum + LLM-side prompt branching all key off these slugs; reordering or renaming silently breaks the cross-stack contract."""

from app.profile.proficiency import ALL_PROFICIENCIES


def test_all_proficiencies_matches_advertised_set() -> None:
    assert (
        frozenset(
            {"beginner", "lower_intermediate", "intermediate", "upper_intermediate", "advanced"}
        )
        == ALL_PROFICIENCIES
    )


def test_all_proficiencies_size_is_five_cefr_bands() -> None:
    assert len(ALL_PROFICIENCIES) == 5
