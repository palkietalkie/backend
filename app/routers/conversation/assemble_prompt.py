"""Assemble the complete system prompt the AI sees for a single conversation.

The orchestrator: it gathers the per-conversation data (persona, profile, location, memory, topic) and composes the section builders (build_persona_section, build_identity_section, build_proficiency_hint, build_natural_phrasing_block) into one prompt. Section-specific text lives in its own build_* module so each reads and tests on its own.
"""

import random

from app.daily_content.models import TalkItem
from app.profile.correction_frequency import coerce_correction_frequency
from app.profile.format_goals_for_prompt import format_goals_for_prompt
from app.routers.conversation.persona_prompt_fields import PersonaPromptFields
from app.routers.conversation.prompt_sections.build_have_a_take_section import (
    build_have_a_take_section,
)
from app.routers.conversation.prompt_sections.build_how_you_talk_section import (
    build_how_you_talk_section,
)
from app.routers.conversation.prompt_sections.build_identity_section import build_identity_section
from app.routers.conversation.prompt_sections.build_ignore_noise_section import (
    build_ignore_noise_section,
)
from app.routers.conversation.prompt_sections.build_laugh_section import build_laugh_section
from app.routers.conversation.prompt_sections.build_make_them_produce_section import (
    build_make_them_produce_section,
)
from app.routers.conversation.prompt_sections.build_natural_phrasing_block import (
    build_natural_phrasing_block,
)
from app.routers.conversation.prompt_sections.build_opening_section import build_opening_section
from app.routers.conversation.prompt_sections.build_partner_first_section import (
    build_partner_first_section,
)
from app.routers.conversation.prompt_sections.build_persona_section import build_persona_section
from app.routers.conversation.prompt_sections.build_proficiency_hint import build_proficiency_hint
from app.routers.conversation.prompt_sections.build_rehearse_section import build_rehearse_section
from app.routers.conversation.prompt_sections.build_take_the_shot_section import (
    build_take_the_shot_section,
)
from app.routers.conversation.prompt_sections.build_their_level_section import (
    build_their_level_section,
)
from app.routers.conversation.prompt_sections.build_todays_news_section import (
    build_todays_news_section,
)
from app.routers.conversation.prompt_sections.build_topic_hook_section import (
    build_topic_hook_section,
)
from app.routers.conversation.prompt_sections.build_using_your_memory_section import (
    build_using_your_memory_section,
)
from app.routers.conversation.prompt_sections.build_when_unclear_section import (
    build_when_unclear_section,
)
from app.services.neon.rows import UserRow
from app.utils.format_local_time import format_local_time


def assemble_prompt(
    persona_fields: PersonaPromptFields,
    user: UserRow,
    kg_entities: list[str],
    today_events_titles: list[str],
    recent_recall: str | None = None,
    topic_override: str | None = None,
    live_city: str | None = None,
    todays_news: list[TalkItem] | None = None,
) -> str:
    name = user["preferred_name"] or "the user"
    # Prefer the device's live city (reverse-geocoded this session) over the profile's location_city: people move and rarely edit the profile field, so the live reading is what actually places the persona in the user's here-and-now. Fall back to the profile, then a generic "their city".
    city = live_city or user["location_city"] or "their city"
    when = format_local_time(user["timezone"])
    target_lang = user["target_language"]
    native_languages = list(user["native_languages"])
    native_languages_phrase = " and ".join(native_languages) if native_languages else "unknown"
    proficiency = user["proficiency"]

    proficiency_hint = build_proficiency_hint(proficiency, target_lang, native_languages_phrase)
    # tutor_speaking_speed is intentionally NOT in the prompt. We tested a prompt pace lever (a target words-per-minute hint) against the real API and it does nothing, the realtime model ignores pace instructions and reverts to ~210 wpm regardless (see app/services/openai/test_manual_openai_speed.py). Tempo is carried entirely by the audio.output.speed post-processing knob set in mint_openai_session; proficiency owns the language/comprehension guidance.

    # Pick one accent at random from the user's selection so users with multiple targets get cycled exposure across sessions. Empty list = no accent steering; the LLM picks whatever its default voice is.
    target_accents = list(user["target_accents"])
    accent_clause = ""
    if target_accents:
        chosen_accent = random.choice(target_accents)  # noqa: S311
        accent_clause = f" Speak in {chosen_accent}."

    stuck_clause = f"If a word doesn't land, drop one quick {native_languages_phrase} word into your next sentence and move on without commentary. Don't announce a pace change."

    # Topic mode: the user tapped a fresh subject on the Today screen. Drop the previous-conversation recall so the session opens clean on the new topic instead of drifting back into it; the carried-over persona character is neutralized inside build_persona_section.
    topic_mode = topic_override is not None
    if topic_mode:
        recent_recall = None
    persona_section = build_persona_section(
        persona_fields, target_lang, name, native_languages_phrase, topic_mode
    )
    identity_section = build_identity_section(name, target_lang)
    partner_first_section = build_partner_first_section(name)
    correction_frequency = coerce_correction_frequency(user["correction_frequency"])
    natural_phrasing_block = build_natural_phrasing_block(name, target_lang, correction_frequency)

    parts: list[str] = [
        "\n\n".join(
            [
                build_how_you_talk_section(name),
                persona_section,
                identity_section,
                build_have_a_take_section(name),
                partner_first_section,
                build_take_the_shot_section(),
                build_their_level_section(proficiency_hint, accent_clause),
                build_opening_section(),
                build_using_your_memory_section(),
                natural_phrasing_block,
                build_when_unclear_section(stuck_clause),
                build_ignore_noise_section(name),
                build_laugh_section(name),
                build_make_them_produce_section(name),
                build_rehearse_section(name),
                build_topic_hook_section(),
            ]
        )
    ]

    parts += [
        "",
        "## Their context",
        f"Location: {city}. Time: {when}.",
    ]

    # Talk-view sessions only (start_conversation passes news=[] in topic mode); grounds the opener's timely hook in real current events instead of date-inference.
    if todays_news:
        parts += ["", build_todays_news_section(todays_news)]

    if user["goals"]:
        goals_text = format_goals_for_prompt(user["goals"])
        parts += ["", "## What they've told you about themselves", f"goals: {goals_text}."]

    # The pronunciation hint AND its meta-instruction only exist when there's actual guidance. Without it, the model uses its own default and we don't waste prompt tokens on a dangling "follow the given pronunciation" instruction with no pronunciation to follow.
    name_pronunciation = (user["name_pronunciation"] or "").strip()
    if name_pronunciation:
        parts += [
            "",
            "## Pronouncing their name",
            f'Say {name}\'s name as: "{name_pronunciation}". Names that look familiar to {target_lang} readers can still be wrong (Ayumi, Nishio, etc.) — follow this pronunciation, not your default.',
        ]

    memory_lines: list[str] = []
    if kg_entities:
        memory_lines.append(
            f"People, places, projects they've mentioned: {', '.join(kg_entities[:10])}."
        )
    if recent_recall:
        memory_lines.append(f"From your last conversations: {recent_recall}")
    if today_events_titles:
        memory_lines.append(f"On their calendar today: {'; '.join(today_events_titles[:5])}.")
    if memory_lines:
        parts += ["", "## What you remember about them"] + memory_lines

    if topic_override:
        parts += ["", "## Today's topic", topic_override]

    return "\n".join(parts)
