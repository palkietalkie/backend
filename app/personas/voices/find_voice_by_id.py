from app.personas.voices.list_voices_for_provider import list_voices_for_provider
from app.personas.voices.voice import Voice


def find_voice_by_id(voice_id: str, provider: str) -> Voice | None:
    for v in list_voices_for_provider(provider):
        if v.id == voice_id:
            return v
    return None
