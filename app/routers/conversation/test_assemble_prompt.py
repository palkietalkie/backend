"""assemble_prompt: pure function that builds the system prompt the AI sees."""

import uuid
from datetime import UTC, datetime

from app.routers.conversation.assemble_prompt import assemble_prompt
from app.routers.conversation.persona_prompt_fields import PersonaPromptFields
from app.services.neon.rows import UserRow


def _user(
    *,
    preferred_name: str | None = "Yuki",
    name_pronunciation: str | None = None,
    native_languages: list[str] | None = None,
    goals: str | None = "job interview prep",
    location_city: str | None = "Tokyo",
    correction_frequency: str = "sometimes",
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
        correction_frequency=correction_frequency,
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


def test_live_city_overrides_stale_profile_city() -> None:
    # People move; the device's live city (this session) must win over the profile's location_city so the persona is placed where the user actually is now.
    out = assemble_prompt(
        PERSONA,
        _user(location_city="Tokyo"),
        kg_entities=[],
        today_events_titles=[],
        live_city="Osaka",
    )
    assert "Osaka" in out
    assert "Tokyo" not in out


def test_falls_back_to_profile_city_when_no_live_city() -> None:
    out = assemble_prompt(
        PERSONA,
        _user(location_city="Tokyo"),
        kg_entities=[],
        today_events_titles=[],
        live_city=None,
    )
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


def test_beginner_is_a_real_from_zero_beginner() -> None:
    # Yas quit Chinese because the old "beginner" threw A1 sentences at a from-zero learner. `beginner` must now scaffold in the native language and explicitly NOT expect sentences.
    user = _user()
    user["proficiency"] = "beginner"
    out = assemble_prompt(PERSONA, user, kg_entities=[], today_events_titles=[])
    # Scaffolds in the user's native language (default Japanese) rather than repeating unparseable English.
    assert "Speak mostly in Japanese" in out
    assert "Do NOT expect sentences" in out
    # Carries its CEFR range so the model can calibrate.
    assert "CEFR pre-A1 to A1" in out


def test_unknown_proficiency_falls_back_to_full_canonical_hint() -> None:
    # Bug guard: an unrecognized proficiency must get the FULL "intermediate" hint, not a stripped default that drifts from the real entry.
    user = _user()
    user["proficiency"] = "not-a-real-level"
    out = assemble_prompt(PERSONA, user, kg_entities=[], today_events_titles=[])
    assert "Intermediate (CEFR B1)" in out


def test_speaking_speed_never_injects_pacing_text() -> None:
    # Speed lives entirely in audio.output.speed (post-processing), never the prompt: a prompt pace lever was tested against the real API and has no effect (the model ignores pace instructions, see test_manual_openai_speed.py), so no per-level pacing phrase, especially a words-per-minute target, may leak into the prompt at any level.
    banned = ["words per minute", "wpm", "Speak slowly", "Speak quickly", "conversational pace"]
    for speed in ("very_slow", "slow", "normal", "fast", "very_fast"):
        user = _user()
        user["tutor_speaking_speed"] = speed
        out = assemble_prompt(PERSONA, user, kg_entities=[], today_events_titles=[])
        for phrase in banned:
            assert phrase not in out


def test_prompt_tells_the_model_not_to_react_to_laughter() -> None:
    # Nao noticed the AI stopped and reacted every time she laughed. The prompt can't stop the VAD interrupting, but it must stop the model treating a laugh as a turn and derailing.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    lowered = out.lower()
    assert "laugh" in lowered
    assert "not a turn" in lowered
    # If a laugh clips the model mid-sentence it should continue, not restart or ask what's funny.
    assert "finish the thought" in lowered


def test_prompt_puts_the_person_before_correction() -> None:
    # Nao's core complaint ("you're just fixing my English", not solving my problem): the AI corrected every turn even when she asked a real question or brought a real problem. The prompt must prioritize engaging as a person over correcting, and it must outrank the natural-phrasing rule.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "Be a real partner first" in out
    assert "Correcting a person who just asked you a real question" in out


def test_prompt_backs_off_corrections_when_user_pushes_back() -> None:
    # When the user signals the correcting is unwanted, the AI must drop it (Nao said it, and the AI ignored her).
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "stop correcting me" in out


def test_prompt_does_not_mandate_correcting_every_turn() -> None:
    # The old prompt demanded correction "non-negotiable, every turn". That absolutism is gone; density is now the user's correction_frequency baseline, and the persona still reads the room via 'Be a real partner first'.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "non-negotiable, every turn" not in out
    assert "Be a real partner first" in out


def test_correction_frequency_never_turns_corrections_off() -> None:
    # `never` = pure conversation partner (Nao's end): the whole teaching section is swapped for an off-note, and none of the correction machinery remains.
    out = assemble_prompt(
        PERSONA, _user(correction_frequency="never"), kg_entities=[], today_events_titles=[]
    )
    assert "corrections turned OFF" in out
    assert "INDEPENDENT of correctness" not in out
    assert "you said X, but a native says Y" not in out


def test_correction_frequency_always_corrects_essentially_everything() -> None:
    # `always` = Wes's end: catch everything, but the teaching machinery (how to correct legibly) is still present.
    out = assemble_prompt(
        PERSONA, _user(correction_frequency="always"), kg_entities=[], today_events_titles=[]
    )
    assert "Correct essentially every gap" in out
    assert "INDEPENDENT of correctness" in out


def test_prompt_states_palkie_talkie_identity_and_mission() -> None:
    # Nao's session: asked "who are you / what is this / what's your name" and the AI dodged (said it had no name, gave a vague answer). The prompt must let the persona name the product (Palkie Talkie) and its mission (get fluent in the target language) when asked.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "Palkie Talkie" in out
    assert "fluent" in out.lower()
    # The mission references the user's actual target language, not a hardcoded "English".
    assert "English" in out  # _user() sets target_language="English"


def test_prompt_can_describe_app_features_when_asked() -> None:
    # Users asked what the app does / what they'd learn and got no answer. The persona should be able to point at real features.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    lowered = out.lower()
    assert "news and quizzes" in lowered
    assert "stats" in lowered


def test_prompt_forbids_repeating_the_same_acknowledgment() -> None:
    # Nao twice called out the AI overusing "Exactly" (in the transcript), and it kept doing it. The prompt must ban repeating the same discourse marker turn after turn.
    out = assemble_prompt(PERSONA, _user(), kg_entities=[], today_events_titles=[])
    assert "Don't repeat the same acknowledgment" in out
    assert "Exactly" in out


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
