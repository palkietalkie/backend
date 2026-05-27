from enum import StrEnum

OPENAI_REALTIME_MODEL = "gpt-realtime-mini"
OPENAI_REALTIME_WS_URL = f"wss://api.openai.com/v1/realtime?model={OPENAI_REALTIME_MODEL}"
OPENAI_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"


# Source of truth: the live ``/v1/realtime/client_secrets`` endpoint itself, which 400s any voice not in this enum. Mirrored from openai-python ``realtime_audio_config_output_param.Voice``. Re-ping when adding a voice.
class OpenAIVoiceId(StrEnum):
    ALLOY = "alloy"
    ASH = "ash"
    BALLAD = "ballad"
    CEDAR = "cedar"
    CORAL = "coral"
    ECHO = "echo"
    MARIN = "marin"
    SAGE = "sage"
    SHIMMER = "shimmer"
    VERSE = "verse"
