from enum import StrEnum

# Realtime model: everyone gets the full model, no tier split. gpt-realtime-2 audio is $32/$64 per 1M in/out ($0.40 cached), the bulk of conversation cost, with GPT-5-class reasoning and a 128K context. A mini tier for the free plan was tried and dropped: it ignores the prompt's explicit prohibitions and parrots "let's slow down" every turn, and conversation quality IS the product.
OPENAI_REALTIME_MODEL_PAID = "gpt-realtime-2"
# Whisper-based realtime STT for the user-side captions/transcript. Chosen over gpt-4o-transcribe because it's whisper (strongly multilingual, so it stops mis-detecting a Japanese speaker's turns as Chinese/Thai/Korean) and it's the only transcription model that exposes the `delay` knob, which buys more audio context before emitting for better accuracy AND better language selection. It costs ~$0.017/min vs gpt-4o-transcribe's ~$0.006/min, but at current volume that's ~$1.50/month total, so the quality wins outright. Not tiered by plan: there's no mini whisper, and the absolute cost is negligible either way. It does NOT support a `prompt`/`language` hint (fine: users code-switch, so we don't want to hard-pin one language anyway).
OPENAI_TRANSCRIPTION_MODEL = "gpt-realtime-whisper"
# How long the transcriber waits for more audio before emitting text. Higher = more context = better accuracy + fewer wrong-language guesses, at the cost of the caption appearing a bit later. Transcription is entirely off the voice-loop critical path (the AI's spoken reply never waits on it), so we can afford a high setting; the only visible effect is the live caption lagging slightly.
OPENAI_TRANSCRIPTION_DELAY = "high"
OPENAI_REALTIME_WS_URL_TEMPLATE = "wss://api.openai.com/v1/realtime?model={model}"
# WebRTC clients POST an SDP offer here instead of opening the WS above; the SDP answer comes back in the response body. Same model + host, its own path — built from the model, not derived from the WS URL.
OPENAI_REALTIME_CALLS_URL_TEMPLATE = "https://api.openai.com/v1/realtime/calls?model={model}"
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
