from app.services.neon.rows import UserRow


def format_user_label(user: UserRow) -> str:
    """Render a UserRow as a human-readable label for Slack messages and logs.

    Preference order: `display_name <email>` → email alone → display_name alone → user id (last resort when both name and email are missing, e.g. fresh Clerk JIT users before profile sync).
    """
    email = user["email"]
    name = user["display_name"]
    if email and name:
        return f"{name} <{email}>"
    return email or name or str(user["id"])
