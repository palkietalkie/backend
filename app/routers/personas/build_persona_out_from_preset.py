import uuid

from pydantic import BaseModel

from app.config import get_settings
from app.personas.presets.preset import Preset


class PersonaOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    voice_id: str
    role: str | None
    age: str | None
    background: str | None
    vocabulary_register: str | None
    conversational_style: str | None
    topical_preferences: str | None
    is_preset: bool
    is_public: bool
    is_owner: bool
    like_count: int
    liked_by_me: bool
    sort_weight: int = 100


def build_persona_out_from_preset(
    p: Preset, *, liked_ids: set[uuid.UUID], like_counts: dict[uuid.UUID, int]
) -> PersonaOut:
    provider = get_settings().inference_provider.lower()
    return PersonaOut(
        id=p.id,
        name=p.name,
        description=p.description,
        voice_id=p.voice_for(provider),
        role=p.role,
        age=p.age,
        background=p.background,
        vocabulary_register=p.vocabulary_register,
        conversational_style=p.conversational_style,
        topical_preferences=p.topical_preferences,
        is_preset=True,
        is_public=True,
        is_owner=False,
        like_count=like_counts.get(p.id, 0),
        liked_by_me=p.id in liked_ids,
        sort_weight=p.sort_weight,
    )
