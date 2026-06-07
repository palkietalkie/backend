"""GET /voices — list the voice catalog for the active inference provider.

The catalog depends on ``INFERENCE_PROVIDER``: PersonaPlex's NATM/NATF/VARM/VARF ids vs OpenAI's named voices. iOS uses this to populate the voice picker on the persona customize screen."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.resolve_current_user import resolve_current_user
from app.config import get_settings
from app.personas.voices.list_voices_for_provider import list_voices_for_provider
from app.services.neon.rows import UserRow

router = APIRouter(prefix="/voices", tags=["voices"])


class VoiceOut(BaseModel):
    id: str
    label: str
    gender: str
    description: str


@router.get("", response_model=list[VoiceOut])
async def list_voices(_user: UserRow = Depends(resolve_current_user)) -> list[VoiceOut]:
    settings = get_settings()
    return [
        VoiceOut(id=v.id, label=v.label, gender=v.gender, description=v.description)
        for v in list_voices_for_provider(settings.inference_provider.lower())
    ]
