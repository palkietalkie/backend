from pydantic import BaseModel, Field

from app.services.neon.rows import PersonaRow

UPDATABLE_FIELDS: tuple[str, ...] = (
    "name",
    "description",
    "voice_id",
    "role",
    "age",
    "background",
    "vocabulary_register",
    "conversational_style",
    "topical_preferences",
    "is_public",
)


class PersonaUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    description: str | None = Field(default=None, max_length=280)
    voice_id: str | None = Field(default=None, max_length=64)
    role: str | None = None
    age: str | None = None
    background: str | None = None
    vocabulary_register: str | None = None
    conversational_style: str | None = None
    topical_preferences: str | None = None
    is_public: bool | None = None


def build_patch_sql(persona: PersonaRow, body: PersonaUpdate) -> tuple[str, list[object]]:
    # Generate an UPDATE statement that only sets fields the caller provided. Trailing param is always the persona id.
    sets: list[str] = []
    values: list[object] = []
    for field in UPDATABLE_FIELDS:
        value = getattr(body, field)
        if value is None:
            continue
        values.append(value)
        sets.append(f"{field} = ${len(values)}")
    if not sets:
        return "", []
    values.append(persona["id"])
    sql = (
        "UPDATE personas SET "
        + ", ".join(sets)
        + ", updated_at = NOW()"
        + f" WHERE id = ${len(values)}"
        + " RETURNING id, name, description, voice_id, role, age, background,"
        + " vocabulary_register, conversational_style, topical_preferences,"
        + " is_public, like_count, user_id, created_at, updated_at"
    )
    return sql, values
