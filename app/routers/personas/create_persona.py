import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.auth.resolve_current_user import resolve_current_user
from app.routers.personas.build_persona_out_from_preset import PersonaOut
from app.routers.personas.build_persona_out_from_row import build_persona_out_from_row
from app.routers.personas.validate_voice import validate_voice
from app.services.neon.db_conn import DBConn
from app.services.neon.get_neon_connection import get_neon_connection
from app.services.neon.make_rows import make_persona_row
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/personas", tags=["personas"])


class PersonaCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=280)
    voice_id: str = Field(min_length=1, max_length=64)
    role: str | None = None
    age: str | None = None
    background: str | None = None
    vocabulary_register: str | None = None
    conversational_style: str | None = None
    topical_preferences: str | None = None
    is_public: bool = False


@router.post("", response_model=PersonaOut, status_code=status.HTTP_201_CREATED)
async def create_persona(
    body: PersonaCreate,
    user: UserRow = Depends(resolve_current_user),
    db: DBConn = Depends(get_neon_connection),
) -> PersonaOut:
    validate_voice(body.voice_id)
    row = await db.fetchrow(
        """INSERT INTO personas (
               id, name, description, voice_id,
               role, age, background,
               vocabulary_register, conversational_style, topical_preferences,
               is_public, user_id
           ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
           RETURNING id, name, description, voice_id, role, age, background,
                     vocabulary_register, conversational_style, topical_preferences,
                     is_public, like_count, user_id, created_at, updated_at""",
        uuid.uuid4(),
        body.name,
        body.description,
        body.voice_id,
        body.role,
        body.age,
        body.background,
        body.vocabulary_register,
        body.conversational_style,
        body.topical_preferences,
        body.is_public,
        user["id"],
    )
    assert row is not None
    persona = make_persona_row(row)
    return build_persona_out_from_row(persona, user_id=user["id"], liked_ids=set())
