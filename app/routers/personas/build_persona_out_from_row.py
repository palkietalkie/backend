import uuid

from app.routers.personas.build_persona_out_from_preset import PersonaOut
from app.services.neon.rows import PersonaRow


def build_persona_out_from_row(
    p: PersonaRow, *, user_id: uuid.UUID, liked_ids: set[uuid.UUID]
) -> PersonaOut:
    return PersonaOut(
        id=p["id"],
        name=p["name"],
        description=p["description"],
        voice_id=p["voice_id"],
        role=p["role"],
        age=p["age"],
        background=p["background"],
        vocabulary_register=p["vocabulary_register"],
        conversational_style=p["conversational_style"],
        topical_preferences=p["topical_preferences"],
        is_preset=False,
        is_public=p["is_public"],
        is_owner=p["user_id"] == user_id,
        like_count=p["like_count"],
        liked_by_me=p["id"] in liked_ids,
    )
