"""assemble_prompt: pure function that builds the system prompt the AI sees."""

import uuid
from datetime import UTC, datetime

from app.routers.conversation.assemble_prompt import PersonaPromptFields, assemble_prompt
from app.services.neon.rows import UserRow


def _user(
    *,
    preferred_name: str | None = "Yuki",
    name_pronunciation: str | None = None,
    native_languages: list[str] | None = None,
    goals: str | None = "job interview prep",
    location_city: str | None = "Tokyo",
) -> UserRow:
    return UserRow(
        id=uuid.uuid4(),
        clerk_user_id="user_x",
        email=None,
        premium=False,
        premium_ends_at=None,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        preferred_name=preferred_name,
        name_pronunciation=name_pronunciation,
        native_languages=native_languages if native_languages is not None else ["Japanese"],
        target_accents=[],
        target_language="English",
        proficiency="intermediate",
        tutor_speaking_speed="normal",
        goals=goals,
        location_city=location_city,
        timezone="Asia/Tokyo",
        personalization_consent=None,
        product_improvement_consent=None,
        consent_screen_seen_at=None,
    )


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
        _user(preferred_name=None, location_city=None),
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
    assert "## Name pronunciation" not in without
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
    assert "## Today's topic" in out
    assert "public speaking" in out


def test_assemble_prompt_topic_mode_drops_persona_character() -> None:
    # A Today-screen topic must NOT carry the previous persona's character (the badminton-coach bleed). The persona's role/name should be absent; a neutral conversation-partner intro replaces it.
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
        topic_override="the James Webb telescope's latest images",
    )
    assert "Aiden" not in out
    assert "dry-comedian" not in out
    assert "James Webb" in out
    assert "no fixed character" in out


def test_assemble_prompt_topic_mode_drops_recall() -> None:
    # Even if recall is passed, topic mode must suppress it so the session doesn't drift back into the last conversation's subject.
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
        recent_recall="user: I love badminton | persona: backhand grip tips",
        topic_override="cooking pasta",
    )
    assert "badminton" not in out
    assert "backhand" not in out
    assert "## What you remember about them" not in out
    assert "cooking pasta" in out


def test_assemble_prompt_correction_examples_are_topic_neutral() -> None:
    # The static correction examples must not be sport-specific — badminton examples in the frame biased every session toward badminton regardless of persona/recall.
    out = assemble_prompt(
        PERSONA, _user(), kg_entities=[], weather_label=None, today_events_titles=[]
    )
    assert "badminton" not in out
    assert "backhand" not in out


def test_assemble_prompt_skips_memory_section_when_empty() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(native_languages=[], goals=None),
        kg_entities=[],
        weather_label=None,
        today_events_titles=[],
    )
    assert "## What you remember about them" not in out


def test_prompt_carries_anti_sycophant_stance() -> None:
    fields = PersonaPromptFields(
        name="Mentor",
        role=None,
        age=None,
        background=None,
        vocabulary_register=None,
        conversational_style=None,
        topical_preferences=None,
    )
    prompt = assemble_prompt(fields, _user(), [], None, [])
    assert "sycophant" in prompt
