from app.asc.app_review_info import DEMO_ACCOUNT_REQUIRED, REVIEW_CONTACT, REVIEW_NOTES


def test_demo_account_not_required_for_sso_only_app() -> None:
    # The app has no username+password, so there's no demo account to hand the reviewer; they use Sign in with Apple instead.
    assert DEMO_ACCOUNT_REQUIRED is False


def test_review_contact_is_complete_and_well_formed() -> None:
    for key in ("first_name", "last_name", "phone", "email"):
        assert REVIEW_CONTACT[key]
    # ASC wants E.164; "@" guards against an obviously broken contact email.
    assert REVIEW_CONTACT["phone"].startswith("+")
    assert "@" in REVIEW_CONTACT["email"]


def test_notes_tell_the_reviewer_to_sign_in_with_apple() -> None:
    # Load-bearing: without this instruction the reviewer hits a login wall (SSO-only, no shared credentials) and rejects the build.
    assert "Sign in with Apple" in REVIEW_NOTES
