from app.services.clerk.clerk_user_payload import ClerkUserPayload
from app.services.clerk.parse_first_name import parse_first_name


def test_first_name_returns_value_or_none() -> None:
    assert parse_first_name(ClerkUserPayload(first_name="Taka")) == "Taka"
    assert parse_first_name(ClerkUserPayload(first_name="")) is None
    assert parse_first_name(ClerkUserPayload(first_name=None)) is None
    assert parse_first_name(ClerkUserPayload()) is None
