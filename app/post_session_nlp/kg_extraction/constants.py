PROMPT_HEADER = """Extract personal-knowledge entities and relations from these user turns.
Entity types: person, place, project, interest, event.
CRITICAL — the speaker (the user) is NOT an entity. Never emit a person entity named "user", "User", "me", "I", or the speaker's own name. To refer to the speaker, always use the exact reserved name "__SELF__". Put the speaker's own attributes (e.g. their weight goal) in the props of a single "__SELF__" entity, and use "__SELF__" as the src or dst for any relationship the speaker has (what they like, do, own, know).
Relations describe how the speaker relates to an entity, or how two entities relate.
Return strict JSON only:
{"entities": [{"type": str, "name": str, "props": {...}}],
 "relations": [{"src": str, "relation": str, "dst": str}]}

Turns:
"""
