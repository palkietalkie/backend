"""Guards the live Clerk instances against a sign-up misconfiguration.

The app is passwordless (email code / Apple / Google) and never collects a password. If a Clerk instance is set to require a password at sign-up, email sign-up silently stalls at `missing_requirements` — a valid code is accepted but NO session is created, and the user is bounced back to the sign-in screen. This exact misconfiguration shipped once. These tests hit the real Frontend API of both instances and fail if password is ever made required again.
"""

import httpx
import pytest

from app.services.clerk.fetch_signup_attributes import fetch_signup_attributes
from app.services.clerk.get_clerk_frontend_api_url import get_clerk_frontend_api_url

# Publishable keys are public by design (they ship inside the iOS app + website); not secrets. Same values as ios/project.yml.
_PUBLISHABLE_KEYS = {
    "dev": "pk_test_Y3V0ZS10aWNrLTQxLmNsZXJrLmFjY291bnRzLmRldiQ",
    "prod": "pk_live_Y2xlcmsucGFsa2lldGFsa2llLmNvbSQ",
}


def test_get_clerk_frontend_api_url_decodes_dev() -> None:
    url = get_clerk_frontend_api_url(_PUBLISHABLE_KEYS["dev"])
    assert url == "https://cute-tick-41.clerk.accounts.dev"


def test_get_clerk_frontend_api_url_decodes_prod() -> None:
    url = get_clerk_frontend_api_url(_PUBLISHABLE_KEYS["prod"])
    assert url == "https://clerk.palkietalkie.com"


@pytest.mark.parametrize("instance", ["dev", "prod"])
async def test_instance_signup_is_passwordless_and_email_enabled(instance: str) -> None:
    try:
        attrs = await fetch_signup_attributes(_PUBLISHABLE_KEYS[instance])
    except httpx.HTTPError:
        pytest.skip(f"Clerk Frontend API for {instance} unreachable (offline)")

    password_required = attrs.get("password", {}).get("required")
    assert password_required is not True, (
        f"Clerk {instance} instance REQUIRES a password at sign-up, but the app is passwordless. "
        "Turn OFF 'Sign-up with password' in User & authentication → Password, "
        "or email sign-up dies at missing_requirements (no session, user bounced to sign-in)."
    )

    email = attrs.get("email_address", {})
    assert email.get("enabled") is True, f"Clerk {instance}: email sign-up/sign-in is disabled"
