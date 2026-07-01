from app.routers.conversation.build_persona_section import build_persona_section
from app.routers.conversation.persona_prompt_fields import PersonaPromptFields

PERSONA = PersonaPromptFields(
    name="Aiden",
    role="dry-comedian",
    age=None,
    background=None,
    vocabulary_register=None,
    conversational_style=None,
    topical_preferences=None,
)


def test_normal_mode_uses_the_persona_character() -> None:
    out = build_persona_section(PERSONA, "English", "Yuki", "Japanese", topic_mode=False)
    assert out.startswith("## Who you are")
    assert "Aiden" in out
    assert "dry-comedian" in out
    assert "Japanese" in out


def test_topic_mode_strips_the_character() -> None:
    # A Today-topic session must not carry the previous persona's name/role (the badminton-coach bleed).
    out = build_persona_section(PERSONA, "English", "Yuki", "Japanese", topic_mode=True)
    assert "Aiden" not in out
    assert "dry-comedian" not in out
    assert "no fixed character" in out
