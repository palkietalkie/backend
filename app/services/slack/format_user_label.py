from app.services.neon.rows import UserRow


def format_user_label(user: UserRow) -> str:
    """Render a UserRow as a human-readable label for Slack messages and logs.

    Preference order: `preferred_name <email>` → email alone → preferred_name alone → user id (last resort when both are missing, e.g. fresh Clerk JIT users before profile sync).
    """
    email = user["email"]
    preferred_name = user["preferred_name"]
    if email and preferred_name:
        return f"{preferred_name} <{email}>"
    return email or preferred_name or str(user["id"])
