"""Read the first name out of a typed Clerk user payload."""

from app.services.clerk.clerk_user_payload import ClerkUserPayload


def parse_first_name(payload: ClerkUserPayload) -> str | None:
    name = (payload.first_name or "").strip()
    return name or None
