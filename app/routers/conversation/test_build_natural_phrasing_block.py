from app.routers.conversation.build_natural_phrasing_block import build_natural_phrasing_block


def test_never_swaps_in_a_corrections_off_note() -> None:
    out = build_natural_phrasing_block("Yuki", "English", "never")
    assert "corrections turned OFF" in out
    # None of the teaching machinery survives at `never`.
    assert "INDEPENDENT of correctness" not in out


def test_always_keeps_the_teaching_frame_and_the_maximal_density_line() -> None:
    out = build_natural_phrasing_block("Yuki", "English", "always")
    assert "Correct essentially every gap" in out
    assert "INDEPENDENT of correctness" in out


def test_the_density_line_matches_the_level() -> None:
    rarely = build_natural_phrasing_block("Yuki", "English", "rarely")
    always = build_natural_phrasing_block("Yuki", "English", "always")
    assert "Correct very sparingly" in rarely
    assert "Correct very sparingly" not in always
