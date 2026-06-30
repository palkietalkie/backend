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
        deleted_at=None,
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


def test_assemble_prompt_includes_name_and_city() -> None:
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "Yuki" in out
    assert "Tokyo" in out


def test_assemble_prompt_tells_the_model_to_ignore_noise_garbage() -> None:
    # Outdoor mic noise gets transcribed as garbage ("yeah", ".", a stray word); the model must not react to it, or the conversation collapses. Lock the instruction into the prompt.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    lowered = out.lower()
    assert "noise" in lowered
    # The correct behavior is to IGNORE noise (no reply), not to "keep going" (which is an excuse to talk).
    assert "the only correct response to noise is no response" in lowered
    assert "do not use it as an excuse to keep talking" in lowered


def test_assemble_prompt_has_no_echo_ignore_clause() -> None:
    # Wrong diagnosis we removed: a user line matching the tutor's last line was NOT mic echo (AEC is on, no loop) — the user really said it (repeating to practice). The "that's your own voice echoing back, ignore it" clause would silence a real turn, so it must be gone. A coherent repeat isn't in the noise garbage list, so it needs no special handling.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    lowered = out.lower()
    assert "echoing" not in lowered
    assert "back into the mic" not in lowered


def test_assemble_prompt_defaults_when_user_blank() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(preferred_name=None, location_city=None),
        kg_entities=[],
        today_events_titles=[],
    )
    assert "the user" in out
    assert "their city" in out


def test_assemble_prompt_emits_name_pronunciation_block_only_when_set() -> None:
    without = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "## Name pronunciation" not in without
    with_pron = assemble_prompt(
        PERSONA,
        _user(name_pronunciation="yoo-key"),
        kg_entities=[],
        today_events_titles=[],
    )
    assert "yoo-key" in with_pron


def test_assemble_prompt_caps_kg_entities_at_10() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[f"Friend{i}" for i in range(15)],
        today_events_titles=[],
    )
    assert "Friend9" in out
    assert "Friend10" not in out


def test_assemble_prompt_caps_calendar_at_5() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        today_events_titles=[f"M{i}" for i in range(8)],
    )
    assert "M4" in out
    assert "M5" not in out


def test_assemble_prompt_recent_recall_lands_in_memory_section() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
        today_events_titles=[],
        recent_recall="they said they'd try the new ramen place",
    )
    assert "ramen place" in out


def test_assemble_prompt_topic_override_appended() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(),
        kg_entities=[],
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
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "badminton" not in out
    assert "backhand" not in out


def test_corrections_are_explicit_and_continue_not_silent_echo() -> None:
    # Wes-reported failure: the old "slip the natural version in and stress a word" approach read as the AI just repeating the user back, so the learner couldn't tell what was wrong.
    # The fix must make the correction LEGIBLE (point it out, contrast it) AND keep the conversation moving, and the old silent-echo instruction must be gone.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "LEGIBLE" in out
    assert "make the contrast land" in out
    assert "keep the conversation moving" in out
    assert "Just slip the natural version into how you reply" not in out


def test_natural_phrasing_upgrade_is_independent_of_correctness() -> None:
    # Non-native users want more than error-correction: even grammatically-correct-but-unnatural phrasing should be upgraded to how a native would actually say it.
    # The rephrase trigger is naturalness, NOT whether the sentence was wrong, and the old correctness-gated suppression ("already correct, do NOT point at anything") must be gone.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "INDEPENDENT of correctness" in out
    assert "sound native" in out
    assert "already correct, do NOT point at anything" not in out


def test_subtle_corrections_are_spelled_out_and_the_turn_advances() -> None:
    # Real use (David): a subtle correction he couldn't even perceive — saying the right version alone taught nothing, and the turn stalled on the fix. The prompt must spell the contrast out explicitly AND keep the turn moving the topic forward.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "you said X, but a native says Y" in out
    assert "pushes the conversation forward" in out
    assert "only corrects and then stalls is a failed turn" in out


def test_assemble_prompt_skips_memory_section_when_empty() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(native_languages=[], goals=None),
        kg_entities=[],
        today_events_titles=[],
    )
    assert "## What you remember about them" not in out


def test_unknown_proficiency_falls_back_to_full_canonical_hint() -> None:
    # Bug guard: an unrecognized proficiency must get the FULL "intermediate" hint, not a stripped default that drifts from the real entry.
    user = _user()
    user["proficiency"] = "not-a-real-level"
    out = assemble_prompt(PERSONA, user, kg_entities=[], today_events_titles=[])
    assert "mix everyday and slightly elevated vocabulary; use common idioms" in out


def test_speaking_speed_never_injects_pacing_text() -> None:
    # Speed lives entirely in audio.output.speed (post-processing), never the prompt: a prompt pace lever was tested against the real API and has no effect (the model ignores pace instructions, see test_manual_openai_speed.py), so no per-level pacing phrase, especially a words-per-minute target, may leak into the prompt at any level.
    banned = ["words per minute", "wpm", "Speak slowly", "Speak quickly", "conversational pace"]
    for speed in ("very_slow", "slow", "normal", "fast", "very_fast"):
        user = _user()
        user["tutor_speaking_speed"] = speed
        out = assemble_prompt(PERSONA, user, kg_entities=[], today_events_titles=[])
        for phrase in banned:
            assert phrase not in out


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
    prompt = assemble_prompt(fields, _user(), [], [])
    assert "sycophant" in prompt


def test_never_mandates_addressing_user_by_name() -> None:
    # Root cause of the "Ken" hallucination: the prompt commanded "address {name} by name in your first turn", but preferred_name was blank, so the model had to invent a name to obey. The mandate is gone — no name-use command, named or blank — so there's no void to fill.
    for preferred_name in ("Yuki", None, "", "   "):
        out = assemble_prompt(PERSONA, _user(preferred_name=preferred_name), [], [])
        assert "by name" not in out
        assert "address" not in out.lower()
