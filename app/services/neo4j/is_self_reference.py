# Every name the extractor might use for the speaker — all resolve to the canonical (:User {id}) node, never an :Entity, so the user's own facts never fragment across "User"/"user"/"me" nodes disconnected from their identity.
# The prompt asks the LLM for "__SELF__"; the rest are defensive fallbacks in case it doesn't comply.
SELF_ALIASES = frozenset({"__self__", "user", "the user", "me", "i", "myself"})


def is_self_reference(entity_name: str, *, user_name: str | None = None) -> bool:
    """True when an extracted entity name refers to the speaker.

    Matches the fixed generic aliases (case/whitespace-insensitive), plus the user's own name when given — so the LLM naming the speaker by their real name (e.g. "Wes") folds onto the User node instead of spawning a duplicate :Entity.
    """
    folded = entity_name.strip().casefold()
    if folded in SELF_ALIASES:
        return True
    return user_name is not None and folded == user_name.strip().casefold()
