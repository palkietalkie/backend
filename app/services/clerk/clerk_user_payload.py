"""Typed view of the subset of Clerk's Backend API user payload we read (extra fields ignored)."""

from pydantic import BaseModel


class ClerkEmailAddress(BaseModel):
    id: str | None = None
    email_address: str | None = None


class ClerkUserPayload(BaseModel):
    first_name: str | None = None
    primary_email_address_id: str | None = None
    email_addresses: list[ClerkEmailAddress] = []
