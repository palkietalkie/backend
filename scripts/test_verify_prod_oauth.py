"""Lock the instance-derivation: a wrong FAPI domain would make the release gate verify the wrong Clerk instance and pass while prod is broken."""

from scripts.verify_prod_oauth import FATAL_IDP_ERRORS, fapi_domain_from_key


def test_fapi_domain_from_prod_key():
    # The real pk_live baked into ios/project.yml Release config.
    assert (
        fapi_domain_from_key("pk_live_Y2xlcmsucGFsa2lldGFsa2llLmNvbSQ") == "clerk.palkietalkie.com"
    )


def test_fapi_domain_from_dev_key():
    assert (
        fapi_domain_from_key("pk_test_Y3V0ZS10aWNrLTQxLmNsZXJrLmFjY291bnRzLmRldiQ")
        == "cute-tick-41.clerk.accounts.dev"
    )


def test_redirect_uri_mismatch_is_fatal():
    # The exact code Google returned for build 1.0(1); the gate must treat it as a hard failure.
    assert "redirect_uri_mismatch" in FATAL_IDP_ERRORS
