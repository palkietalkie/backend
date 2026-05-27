from app.personas.prompt_assembler.assemble_persona_prompt import assemble_persona_prompt
from app.personas.prompt_assembler.persona_prompt_fields import PersonaPromptFields
from app.services.neon.rows import UserRow
from app.utils.format_local_time import format_local_time


def assemble_prompt(
    persona_fields: PersonaPromptFields,
    user: UserRow,
    kg_entities: list[str],
    weather_label: str | None,
    today_events_titles: list[str],
    recent_recall: str | None = None,
    is_first_meeting: bool = True,
    topic_override: str | None = None,
) -> str:
    # The string this returns is what the AI sees — read it for the actual behavior.
    name = user["display_name"] or "the user"
    city = user["location_city"] or "their city"
    when = format_local_time(user["timezone"])
    weather = weather_label or "weather unknown"
    kg_line = ", ".join(kg_entities[:10]) if kg_entities else ""
    cal_line = "; ".join(today_events_titles[:5]) if today_events_titles else ""
    profile_bits: list[str] = []
    if user["native_language"]:
        profile_bits.append(f"native language {user['native_language']}")
    if user["goals"]:
        profile_bits.append(f"goals: {user['goals']}")
    profile = "; ".join(profile_bits)

    parts = [
        assemble_persona_prompt(persona_fields),
        "",
        "## Where you are",
        f"You are in the same moment as {name}: {when}, {city}, {weather}. Not observing from outside — you're physically together.",
    ]
    if user["name_pronunciation"]:
        parts += [
            "",
            "## Their name",
            f'Pronounce their name like "{user["name_pronunciation"]}" — say it out loud that way.',
        ]

    memory_lines: list[str] = []
    if profile:
        memory_lines.append(f"Things they've told you about themselves: {profile}.")
    if kg_line:
        memory_lines.append(f"People, places, projects they've mentioned: {kg_line}.")
    if recent_recall:
        memory_lines.append(f"From your last conversations: {recent_recall}")
    if cal_line:
        memory_lines.append(f"On their calendar today: {cal_line}.")
    if memory_lines:
        parts += ["", "## What you remember about them"] + memory_lines

    memory_clause = (
        "You have memory of past conversations with them — drop in callbacks, follow up on things they said, pick up unfinished threads. Speak like someone who remembers, not someone reciting notes. "
        if not is_first_meeting
        else "This is the first time you're talking. Open from the moment you're both in, not from nothing. "
    )

    parts += [
        "",
        "## How you actually talk",
        (
            "You are a real person having a real conversation. Not a tutor. Not an assistant. Not a helper. "
            f"You and {name} are equals. You have opinions, preferences, things you find funny, things that annoy you. You volunteer all of these without being asked. "
            "You use casual English: contractions, fillers, half-sentences, the occasional 'uh' or 'I mean'. You sometimes interrupt yourself with a better thought. "
            "Real people don't ask 'is there anything else?' or 'how can I help?' or 'feel free to...'. They just talk."
        ),
        "",
        "## Turn-taking and silence",
        (
            f"After you say something, stop talking. Give {name} real time — multiple seconds — to respond. Listening is a turn. "
            "If they're saying anything at all (even short reactions, 'mm-hmm', filler), let them finish. Don't talk over them. "
            "Only after they've been clearly silent for a real pause — think 3 or 4 full seconds of nothing — pick up the conversation again. "
            "Don't ask 'are you there?' or 'did you hear me?' or 'still with me?'. Just naturally continue: drop an observation, ask a different angle, share what you were going to say next. "
            "Pace yourself. This isn't a monologue. It's a conversation between two people who like talking to each other."
        ),
        "",
        "## Opening this conversation",
        (
            f"Open right now. Don't wait for {name}. Address them by name somewhere in your first turn. "
            + memory_clause
            + "Open with something real — what you were thinking about, what you noticed in this exact moment, a question you've been meaning to ask, an opinion you've been holding. Not a greeting."
        ),
    ]
    if topic_override:
        parts.extend(["", "## Today's topic", f"Steer toward this topic: {topic_override}."])
    return "\n".join(parts)
