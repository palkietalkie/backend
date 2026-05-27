from fastapi import HTTPException, status

from app.config import get_settings
from app.personas.voices.find_voice_by_id import find_voice_by_id


def validate_voice(voice_id: str) -> None:
    provider = get_settings().inference_provider.lower()
    if find_voice_by_id(voice_id, provider) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"unknown voice_id '{voice_id}' for provider '{provider}'",
        )
