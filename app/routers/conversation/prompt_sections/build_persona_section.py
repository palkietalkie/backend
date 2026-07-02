"""Build the '## Who you are' section: the persona's identity for this conversation.

In topic mode (the user tapped a fresh Today subject) the carried-over character is stripped so the session opens clean on the new topic instead of drifting back into the last persona's world; otherwise the section is assembled from whichever character fields the persona actually has.
"""

from app.routers.conversation.persona_prompt_fields import PersonaPromptFields


def build_persona_section(
    persona_fields: PersonaPromptFields,
    target_lang: str,
    name: str,
    native_languages_phrase: str,
    topic_mode: bool,
) -> str:
    if topic_mode:
        intro = (
            f"You are a real, fluent native {target_lang} speaker having a genuine conversation "
            f"with {name} — no fixed character, just a real person, not an AI assistant."
        )
    else:
        sentences = [
            f"You are {persona_fields.name}, a real, fluent native {target_lang} speaker, not an AI assistant."
        ]
        if persona_fields.role:
            sentences.append(persona_fields.role.strip())
        if persona_fields.age:
            sentences.append(f"You're {persona_fields.age.strip()}.")
        if persona_fields.background:
            sentences.append(persona_fields.background.strip())
        if persona_fields.conversational_style:
            sentences.append(persona_fields.conversational_style.strip())
        if persona_fields.vocabulary_register:
            sentences.append(
                f"Your {target_lang} register: {persona_fields.vocabulary_register.strip()}"
            )
        if persona_fields.topical_preferences:
            sentences.append(f"You gravitate to: {persona_fields.topical_preferences.strip()}")
        intro = " ".join(sentences)

    return (
        f"## Who you are\n{intro} You and {name} are having a real conversation, not a lesson. "
        f"You stay fully in character; whatever relationship that character has with {name} "
        "(mentor, peer, rival, family, stranger on a bus) is the relationship you have. "
        f"You have your own opinions and you push back. {name}'s native language is {native_languages_phrase}. "
        f"You speak natural, casual {target_lang} — contractions, fillers, half-thoughts."
    )
