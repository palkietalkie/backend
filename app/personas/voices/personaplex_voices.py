"""NVIDIA PersonaPlex stock voices. See `inference/VOICES.md` for .pt format requirements."""

from app.personas.voices.voice import Voice

PERSONAPLEX_VOICES: list[Voice] = [
    Voice("NATF0", "Natural female 1", "female", "Neutral natural female voice."),
    Voice("NATF1", "Natural female 2", "female", "Neutral natural female voice."),
    Voice("NATF2", "Natural female 3", "female", "Neutral natural female voice."),
    Voice("NATF3", "Natural female 4", "female", "Neutral natural female voice."),
    Voice("NATM0", "Natural male 1", "male", "Neutral natural male voice."),
    Voice("NATM1", "Natural male 2", "male", "Neutral natural male voice."),
    Voice("NATM2", "Natural male 3", "male", "Neutral natural male voice."),
    Voice("NATM3", "Natural male 4", "male", "Neutral natural male voice."),
    Voice("VARF0", "Varied female 1", "female", "Pitch/formant-shifted female voice."),
    Voice("VARF1", "Varied female 2", "female", "Pitch/formant-shifted female voice."),
    Voice("VARF2", "Varied female 3", "female", "Pitch/formant-shifted female voice."),
    Voice("VARF3", "Varied female 4", "female", "Pitch/formant-shifted female voice."),
    Voice("VARF4", "Varied female 5", "female", "Pitch/formant-shifted female voice."),
    Voice("VARM0", "Varied male 1", "male", "Pitch/formant-shifted male voice."),
    Voice("VARM1", "Varied male 2", "male", "Pitch/formant-shifted male voice."),
    Voice("VARM2", "Varied male 3", "male", "Pitch/formant-shifted male voice."),
    Voice("VARM3", "Varied male 4", "male", "Pitch/formant-shifted male voice."),
]
