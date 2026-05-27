"""assemble_prompt: pure function that builds the system prompt the AI sees."""

import uuid
from datetime import UTC, datetime

from app.personas.prompt_assembler.persona_prompt_fields import PersonaPromptFields
from app.routers.conversation.assemble_prompt import assemble_prompt
from app.services.neon.rows import UserRow


def _user(**overrides: object) -> UserRow:
    base: UserRow = UserRow(
        id=uuid.uuid4(),
        clerk_user_id="user_x",
        email=None,
        premium=False,
        premium_ends_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        display_name="Yuki",
        name_pronunciation=None,
        native_language="ja",
        target_accent=None,
        goals="job interview prep",
        location_city="Tokyo",
        timezone="Asia/Tokyo",
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
    )
    base.update(overrides)  # type: ignore[typeddict-item]
    return base


PERSONA = PersonaPromptFields(
    name="Aiden",
    role="dry-comedian",
    age=None,
    background=None,
    vocabulary_register=None,
    conversational_style=None,
    topical_preferences=None,
)


def test_assemble_prompt_includes_name_city_weather() -> None:
    out = assemble_prompt(
        PERSONA, _user(), kg_entities=[], weather_label="cloudy", today_events_titles=[]
    )
    assert "Yuki" in out
    assert "Tokyo" in out
    assert "cloudy" in out


def test_assemble_prompt_defaults_when_user_blank() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(display_name=None, location_city=None),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
    )
    assert "the user" in out
    assert "their city" in out
    assert "weather unknown" in out


def test_assemble_prompt_emits_name_pronunciation_block_only_when_set() -> None:
    without = assemble_prompt(
        PERSONA, _user(), kg_entities=[], weather_label="x", today_events_titles=[]
    )
    assert "Pronounce their name" not in without
    with_pron = assemble_prompt(
        PERSONA,
        _user(name_pronunciation="yoo-key"),
        kg_entities=[],
        weather_label="x",
        today_events_titles=[],
    )
    assert "yoo-key" in with_pron


def test_assemble_prompt_caps_kg_entities_at_10() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[f"Friend{i}" for i in range(15)],
        weather_label=None,
        today_events_titles=[],
    )
    assert "Friend9" in out
    assert "Friend10" not in out


def test_assemble_prompt_caps_calendar_at_5() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[f"M{i}" for i in range(8)],
    )
    assert "M4" in out
    assert "M5" not in out


def test_assemble_prompt_returning_user_drops_first_meeting_line() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
        is_first_meeting=False,
    )
    assert "first time you're talking" not in out
    assert "callbacks" in out


def test_assemble_prompt_recent_recall_lands_in_memory_section() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
        recent_recall="they said they'd try the new ramen place",
    )
    assert "ramen place" in out


def test_assemble_prompt_topic_override_appended() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
        topic_override="public speaking",
    )
    assert "Today's topic" in out
    assert "public speaking" in out


def test_assemble_prompt_skips_memory_section_when_empty() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(native_language=None, goals=None),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
    )
    assert "What you remember about them" not in out
