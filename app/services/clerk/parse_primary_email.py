"""Pick the primary email out of a typed Clerk user payload."""

from app.services.clerk.clerk_user_payload import ClerkUserPayload


def parse_primary_email(payload: ClerkUserPayload) -> str | None:
    """The primary email, falling back to the first address that has one, then None."""
    primary = next(
        (
            a.email_address
            for a in payload.email_addresses
            if a.email_address and a.id == payload.primary_email_address_id
        ),
        None,
    )
    if primary:
        return primary
    return next((a.email_address for a in payload.email_addresses if a.email_address), None)
