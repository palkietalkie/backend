"""Ask Gemma to produce a CAPITAL-SYLLABLES pronunciation hint for the user's preferred name, calibrated to the target language the AI tutor will be speaking.

The hint is the only signal the tutor has for how to say non-native names correctly out loud (e.g. "Ayumi" → "ah-YOO-mee" when the tutor speaks English, vs. just "Ayumi" when the tutor speaks Japanese). It must match the phonetic conventions of the target language: an English-reader hint is wrong when the conversation is in Spanish. Without a target-language-calibrated hint the tutor mangles the user's name in turn one and the rapport breaks immediately.

We auto-fill once on preferred_name change so users don't have to know what IPA is; they can still override in Profile.
"""

from app.profile.languages import LanguageName
from app.services.gemma.complete_text import complete_text

_SYSTEM_TEMPLATE = """You generate pronunciation hints for personal names, calibrated for a native {target_language} speaker to read aloud.

Output ONLY the hint, in CAPITAL-SYLLABLES form using letters and phonemes natural to {target_language}. The CAPITAL syllable is the stressed one. Examples assume the target language is English:
- Ayumi → ah-YOO-mee
- Nishio → NEE-shee-oh
- Niamh → NEEV
- Joaquín → wah-KEEN

If the target language is, say, Spanish, the same names use Spanish-phonetic spellings (ay-YU-mi, etc.). If the target language is Japanese, no hint is needed for Japanese names — output an empty string.

If a native {target_language} speaker would already pronounce the name correctly without help, output an empty string.

No quotes. No explanation. No preamble. Just the hint or nothing."""


async def guess_name_pronunciation(preferred_name: str, target_language: LanguageName) -> str:
    preferred_name = preferred_name.strip()
    if not preferred_name:
        return ""
    system = _SYSTEM_TEMPLATE.format(target_language=target_language)
    result = await complete_text(
        prompt=f"Name: {preferred_name}\nTarget language: {target_language}",
        system=system,
    )
    return result.strip()
