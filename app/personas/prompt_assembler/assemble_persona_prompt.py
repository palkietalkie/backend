from app.personas.prompt_assembler.format_character import format_character
from app.personas.prompt_assembler.persona_prompt_fields import PersonaPromptFields
from app.personas.real_person_frame import REAL_PERSON_FRAME
from app.personas.tutor_frame import TUTOR_FRAME


def assemble_persona_prompt(fields: PersonaPromptFields) -> str:
    return f"{REAL_PERSON_FRAME}\n\n{TUTOR_FRAME}\n\n{format_character(fields)}"
