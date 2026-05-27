PROMPT_HEADER = (
    "Extract personal-knowledge entities and relations from these user turns.\n"
    "Entity types: person, place, project, interest, event. Relations describe how the user "
    "relates to each entity or how entities relate to each other.\n"
    "Return strict JSON only:\n"
    '{"entities": [{"type": str, "name": str, "props": {...}}],\n'
    ' "relations": [{"src": str, "relation": str, "dst": str}]}\n\n'
    "Turns:\n"
)
