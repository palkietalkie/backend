from app.profile.goal import GOAL_PROMPT_PHRASES


def format_goals_for_prompt(goals: str) -> str:
    """Humanize the stored goals string for the system prompt.

    `goals` is a comma-joined mix of preset slugs (app/profile/goal.py) and free-text "Other" entries. Map each known slug to its readable phrase so the tutor never hears "dating_relationships"; leave free-text "Other" entries untouched. Re-joins with ", " so a free-text fragment that itself contains a comma is reconstructed intact (only exact slug tokens are translated)."""
    # str-keyed view: the source dict is keyed by the Goal Literal, but the parts we look up are arbitrary strings (free text), so the lookup key type must be str.
    phrases: dict[str, str] = {str(slug): phrase for slug, phrase in GOAL_PROMPT_PHRASES.items()}
    parts = [p.strip() for p in goals.split(",") if p.strip()]
    return ", ".join(phrases.get(p, p) for p in parts)
