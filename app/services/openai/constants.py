from enum import StrEnum

OPENAI_REALTIME_MODEL_PAID = "gpt-realtime"
OPENAI_REALTIME_MODEL_FREE = "gpt-realtime-mini"
OPENAI_TRANSCRIPTION_MODEL_PAID = "gpt-4o-transcribe"
OPENAI_TRANSCRIPTION_MODEL_FREE = "gpt-4o-mini-transcribe"
OPENAI_REALTIME_WS_URL_TEMPLATE = "wss://api.openai.com/v1/realtime?model={model}"
OPENAI_CLIENT_SECRETS_URL = "https://api.openai.com/v1/realtime/client_secrets"
# Classic single-shot TTS endpoint. Limited voice set (alloy, ash, coral, echo, sage, shimmer) — for the realtime-only voices use the Realtime API one-shot via /v1/responses (see synthesize_speech_realtime).
OPENAI_TTS_URL = "https://api.openai.com/v1/audio/speech"
OPENAI_TTS_MODEL = "tts-1-hd"
# Chat Completions audio modality — accepts a voice + text and returns base64-encoded audio inline. Covers `ballad` on top of the TTS-1 set; `cedar`/`marin`/`verse` are still WebSocket-Realtime-only. Model id renamed from `gpt-4o-audio-preview` → `gpt-audio-mini` in the late-2025 lineup.
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_CHAT_AUDIO_MODEL = "gpt-audio-mini"


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
