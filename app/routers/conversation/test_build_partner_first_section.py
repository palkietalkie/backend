from app.routers.conversation.build_partner_first_section import build_partner_first_section


def test_prioritizes_the_person_and_backs_off_on_pushback() -> None:
    out = build_partner_first_section("Yuki")
    assert out.startswith("## Be a real partner first")
    # Answer real questions instead of deflecting into a lesson.
    assert "ANSWER it" in out
    # Drop corrections the moment the user pushes back.
    assert "stop correcting me" in out
    # It's the override that outranks the correction mechanics.
    assert "outranks the natural-phrasing rule" in out
