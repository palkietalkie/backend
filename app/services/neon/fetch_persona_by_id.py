import uuid

from app.services.neon.db_conn import DBConn
from app.services.neon.rows import PersonaRow


async def fetch_persona_by_id(db: DBConn, persona_id: uuid.UUID) -> PersonaRow | None:
    row = await db.fetchrow(
        """SELECT id, name, description, voice_id, role, age, background,
                  vocabulary_register, conversational_style, topical_preferences,
                  is_public, like_count, user_id, created_at, updated_at
           FROM personas
           WHERE id = $1""",
        persona_id,
    )
    return dict(row) if row is not None else None  # type: ignore[return-value]
