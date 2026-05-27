VALID_CATEGORIES: frozenset[str] = frozenset(
    {"article", "preposition", "tense", "word_choice", "naturalness"}
)


PROMPT_HEADER = (
    "You are reviewing a non-native English speaker's transcript turns for mistakes.\n"
    "Only flag genuine errors. Categories must be one of: article, preposition, tense, "
    "word_choice, naturalness.\n"
    'Return strict JSON: {"mistakes": [{"original": str, "corrected": str, '
    '"category": str}]}. No prose.\n\n'
    "Turns:\n"
)
