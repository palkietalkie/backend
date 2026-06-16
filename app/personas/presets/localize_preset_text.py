from app.personas.presets.preset_text_translations import PRESET_TEXT


def localize_preset_text(text: str, lang: str) -> str:
    # Preset CONTENT is backend-owned; serve the client's language, fall back to the canonical English.
    return PRESET_TEXT.get(text, {}).get(lang, text)
