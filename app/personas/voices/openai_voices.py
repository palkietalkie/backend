"""OpenAI Realtime voices.

Live catalog, validated by /v1/realtime/sessions itself — see SUPPORTED_OPENAI_VOICES in
services/openai/constants.py.
"""

from app.personas.voices.voice import Voice

OPENAI_VOICES: list[Voice] = [
    Voice("alloy", "Alloy", "neutral", "Neutral, even-toned."),
    Voice("ash", "Ash", "male", "Warm, grounded male voice."),
    Voice("ballad", "Ballad", "female", "Warm, melodic female voice."),
    Voice("coral", "Coral", "female", "Bright, clear female voice."),
    Voice("echo", "Echo", "male", "Measured, resonant male voice."),
    Voice("sage", "Sage", "neutral", "Thoughtful, even-paced."),
    Voice("shimmer", "Shimmer", "female", "Light, friendly female voice."),
    Voice("verse", "Verse", "male", "Expressive, commanding male voice."),
    Voice("marin", "Marin", "female", "Warm conversational female voice."),
    Voice("cedar", "Cedar", "male", "Firm, steady male voice."),
]
