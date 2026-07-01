from dataclasses import dataclass


@dataclass(frozen=True)
class PersonaPromptFields:
    name: str
    role: str | None
    age: str | None
    background: str | None
    vocabulary_register: str | None
    conversational_style: str | None
    topical_preferences: str | None
