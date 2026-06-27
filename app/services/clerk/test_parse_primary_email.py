from app.services.clerk.clerk_user_payload import ClerkEmailAddress, ClerkUserPayload
from app.services.clerk.parse_primary_email import parse_primary_email


def test_primary_email_picks_the_address_matching_primary_id() -> None:
    payload = ClerkUserPayload(
        primary_email_address_id="idn_2",
        email_addresses=[
            ClerkEmailAddress(id="idn_1", email_address="old@example.com"),
            ClerkEmailAddress(id="idn_2", email_address="primary@example.com"),
        ],
    )
    assert parse_primary_email(payload) == "primary@example.com"


def test_primary_email_falls_back_to_first_when_id_unmatched() -> None:
    payload = ClerkUserPayload(
        primary_email_address_id="missing",
        email_addresses=[ClerkEmailAddress(id="idn_1", email_address="only@example.com")],
    )
    assert parse_primary_email(payload) == "only@example.com"


def test_primary_email_none_when_no_addresses() -> None:
    assert parse_primary_email(ClerkUserPayload()) is None
