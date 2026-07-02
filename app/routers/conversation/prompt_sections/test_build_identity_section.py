from app.routers.conversation.prompt_sections.build_identity_section import build_identity_section


def test_names_the_product_mission_and_features() -> None:
    out = build_identity_section("Yuki", "English")
    assert out.startswith("## What you are, if they ask")
    assert "Palkie Talkie" in out
    # Mission references the user's actual target language.
    assert "English" in out
    # Can point at real features when asked.
    assert "news and quizzes" in out
    assert "stats" in out
