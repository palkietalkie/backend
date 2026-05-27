from app.personas.prompt_assembler.persona_prompt_fields import PersonaPromptFields


def format_character(fields: PersonaPromptFields) -> str:
    parts: list[str] = []
    if fields.role:
        parts.append(fields.role.strip())
    extras: list[str] = []
    if fields.age:
        extras.append(f"Age: {fields.age.strip()}")
    if fields.background:
        extras.append(f"Background: {fields.background.strip()}")
    if fields.vocabulary_register:
        extras.append(f"Vocabulary: {fields.vocabulary_register.strip()}")
    if fields.conversational_style:
        extras.append(f"Style: {fields.conversational_style.strip()}")
    if fields.topical_preferences:
        extras.append(f"Topics: {fields.topical_preferences.strip()}")
    if extras:
        parts.append(" ".join(extras))
    if not parts:
        return f"You are a real person named after the persona '{fields.name}'. You are not an assistant. You volunteer opinions, ask follow-ups, fill silence naturally."
    return "\n".join(parts)
