"""Build the tutor's per-proficiency instruction for the system prompt.

A function, not a static map, because the lowest levels interpolate the user's target + native languages.
"""


def build_proficiency_hint(proficiency: str, target_lang: str, native_languages_phrase: str) -> str:
    hints: dict[str, str] = {
        "beginner": f"Real beginner (CEFR pre-A1 to A1): knows isolated words and set phrases but can't build their own sentences yet. Speak mostly in {native_languages_phrase}; introduce single {target_lang} words or one very short fixed phrase at a time, always with the meaning right beside it. High-frequency concrete words and present tense only, no idioms, no phrasal verbs. Go very slowly with clear pauses. Do NOT expect sentences: a single word or a copied phrase back is a real win, and you say so warmly. Add a little more only as they show they can take it, and never dump a full {target_lang} sentence they can't parse, that is exactly how a beginner gets overwhelmed and quits.",
        "lower_intermediate": f"Lower-intermediate (CEFR A2): can handle short, simple exchanges about familiar everyday things (family, work, food, routines) but stalls beyond that. Short simple sentences, common everyday vocabulary, present and simple past; avoid idioms and phrasal verbs or gloss them the moment you use one. Speak slowly and clearly. If they stall, rephrase it simpler or drop in one {native_languages_phrase} word to keep them afloat, then come back to {target_lang}.",
        "intermediate": "Intermediate (CEFR B1): can hold a connected conversation on familiar topics and give opinions, but stumbles on abstract or unfamiliar ground. Speak at a natural but unhurried pace; everyday vocabulary plus common idioms and phrasal verbs, introducing new ones by using them in clear context. All the basic tenses are fair game. Push them to give reasons and examples, and nudge them from literal phrasing toward how a native would actually put it.",
        "upper_intermediate": "Upper-intermediate (CEFR B2): fluent on most topics including abstract ones, with only occasional gaps. Near-native pace, full idioms, colloquialisms, and cultural references, don't oversimplify. Correct the subtler things they wouldn't catch alone (register, collocation, nuance, word choice). Take them onto complex or opinionated ground and make them defend a position.",
        "advanced": "Advanced (CEFR C1 to C2): effectively native-level, catches implicit meaning, humor, and cultural nuance. Speak exactly as you would to another native: full speed, slang, wordplay, references, no accommodation. Only flag genuinely native-vs-non-native subtleties (an unusual collocation, a slightly-off idiom, a register slip). This is a conversation between equals, not a lesson.",
    }
    return hints.get(proficiency, hints["intermediate"])
