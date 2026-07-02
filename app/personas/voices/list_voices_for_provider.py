from app.personas.voices.openai_voices import OPENAI_VOICES
from app.personas.voices.personaplex_voices import PERSONAPLEX_VOICES
from app.personas.voices.voice import Voice


def list_voices_for_provider(provider: str) -> list[Voice]:
    # openai_webrtc shares the OpenAI voice catalog (same models + voices, only the transport differs).
    if provider in ("openai", "openai_webrtc"):
        return OPENAI_VOICES
    return PERSONAPLEX_VOICES
